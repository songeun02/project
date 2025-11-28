import os
import time
from pathlib import Path
import pandas as pd

import folium
import geopandas as gpd

import pulp
from math import sqrt
from shapely.geometry import Point
from shapely.geometry import Polygon

from tabulate import tabulate

def compute_coverage_matrix(demand_df, cand_df, coverage_radius):
    '''
        커버리지 매트릭스 계산
        demand_df : 수요지점 데이터프레임
        cand_df : 후보지점 데이터프레임
        coverage_radius : 커버리지 반경 (단위: m)
    '''
    cov = {}
    print('커버 반경 계산 시작')
    for _, d in demand_df.iterrows():
        for _, c in cand_df.iterrows():
            dist = sqrt((d.x - c.x)**2 + (d.y - c.y)**2)
            cov[(d.id, c.id)] = 1 if dist <= coverage_radius else 0
    print('커버 반경 계산 완료')
    return cov

def calMclp(demand_df, cand_df,p_num,coverage_radius, WEIGHT):
    '''
        MCLP 문제
        demand_df : 수요지점 데이터프레임
        cand_df : 후보지점 데이터프레임
        coverage_radius : 커버리지 반경 (단위: m)
    '''
    coverage = compute_coverage_matrix(demand_df, cand_df, coverage_radius)

    p = p_num
    prob = pulp.LpProblem(f"MCLP_p_{p}", pulp.LpMaximize)

    x = {c: pulp.LpVariable(f"x_{c}", cat="Binary") for c in cand_df['id']}
    y = {d: pulp.LpVariable(f"y_{d}", cat="Binary") for d in demand_df['id']}

    if WEIGHT:
        # 가중치 있는 목적함수: 커버된 수요지들의 가중치 합 최대화
        weight_dict = demand_df.set_index('id')['w'].to_dict()
        prob += pulp.lpSum(weight_dict[d] * y[d] for d in demand_df['id'])
        #prob += pulp.lpSum(demand_df.loc[demand_df['id'] == d, 'weight'].values[0] * y[d] for d in demand_df['id'])
    else:
        # 가중치 없는 목적함수: 커버된 수요지 개수 최대화
        prob += pulp.lpSum(y[d] for d in demand_df['id'])

    print('목적함수 추가 완료')

    # 제약조건 1: 수요지 d는 적어도 하나의 시설 c로 커버될 때만 y[d] = 1
    for d in demand_df['id']:
        prob += y[d] <= pulp.lpSum(coverage[(d, c)] * x[c] for c in cand_df['id'])
    print('제약조건1 추가완료')

    # 제약조건 2: 설치할 수 있는 후보지 수는 p개로 제한
    prob += pulp.lpSum(x[c] for c in cand_df['id']) == p
    print('제약조건2 추가완료')

    # 최적화 수행
    print('최적화 시작')
    prob.solve(pulp.PULP_CBC_CMD(msg=False))
    print('최적화 완료')

    # 결과 추출
    print('결과 추출 시작')
    selected_cands = [c for c in cand_df['id'] if pulp.value(x[c]) >= 0.5]
    covered_demand = [d for d in demand_df['id'] if pulp.value(y[d]) >= 0.5]
    print('결과 추출 완료')

    print("선정된 후보지:", selected_cands)
    print("커버된 수요지:", covered_demand)

    return demand_df, cand_df, selected_cands, covered_demand


def makeGeodf(demand_df, cand_df, selected_cands, covered_demand):
    '''
        GeoDataFrame으로 변환
        demand_df : 수요지점 데이터프레임
        cand_df : 후보지점 데이터프레임
        selected_cand : 선정된 후보지
        covered_demand : 커버된 수요지
    '''
    demand_gdf = gpd.GeoDataFrame(
        demand_df, geometry=gpd.points_from_xy(demand_df.x, demand_df.y), crs="EPSG:5186"
    )
    cand_gdf = gpd.GeoDataFrame(
        cand_df, geometry=gpd.points_from_xy(cand_df.x, cand_df.y), crs="EPSG:5186"
    )
    print('GeoDataFrame 변환 완료')

    demand_gdf["covered"] = demand_gdf["id"].apply(lambda i: 1 if i in covered_demand else 0)
    cand_gdf["selected"] = cand_gdf["id"].apply(lambda i: 1 if i in selected_cands else 0)
    print('GeoDataFrame 전처리 완료')

    return demand_gdf, cand_gdf


def drawMap(demand_gdf, cand_gdf, coverage_radius,gungu,p_num,meter,SAVE_PATH, ca):
    '''
        folium으로 실제 지도에 쓰레기통 입지 시각화
        demand_gdf : 수요입지 지오데이터프레임
        cand_gdf : 후보입지 지오데이터프레임
        covera_radius : 커버 반경
        SAVE_PATH : 시각화 링크 저장 경로
    '''

    # 5186 -> 4326 변환
    demand_gdf4326 = demand_gdf.to_crs(epsg=4326)
    cand_gdf4326 = cand_gdf.to_crs(epsg=4326)

    center = [demand_gdf4326.geometry.y.mean(), demand_gdf4326.geometry.x.mean()]
    m = folium.Map(location=center, zoom_start=12)

    # 수요지
    for _, row in demand_gdf4326.iterrows():
        color = "green" if row["covered"] == 1 else "red"
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=5,
            color=color,
            fill=True,
            fill_color=color,
            popup=f"수요지 {row['id']}"
        ).add_to(m)
    print('수요지 지도 표시 완료')

    # 선정된 후보지만 지도에 표시
    selected_candidates = cand_gdf4326[cand_gdf4326["selected"] == 1]

    for _, row in selected_candidates.iterrows():
        folium.Marker(
            location=[row.geometry.y, row.geometry.x],
            popup=f"선정된 후보지 {row['id']}",
            icon=folium.Icon(color="blue", icon="ok-sign")
        ).add_to(m)

        # 커버 범위(coverage radius)도 함께 표시
        folium.Circle(
            radius=coverage_radius,
            location=[row.geometry.y, row.geometry.x],
            color="blue",
            fill=True,
            fill_opacity=0.15
        ).add_to(m)
    print('선정된 후보지만 지도 표시 완료')

    m.save(f"../{SAVE_PATH}/{ca}/시각화/{gungu}/{meter}/mclp_result_{gungu}_{p_num}개_map.html")
    print(f'{ca} {meter} p={p_num} 지도 html 파일 저장완료')

    return [demand_gdf4326, cand_gdf4326]

def getWgs(gdf4326_list):
    result = []
    for i, df in enumerate(gdf4326_list):
        df['WGS4326_x']=df.geometry.x
        df['WGS4326_y']=df.geometry.y
        if i == 0 : cols = ['id', '군구', '행정동', 'x', 'y', 'WGS4326_x','WGS4326_y','covered']
        else: cols = ['id', 'x', 'y', 'WGS4326_x','WGS4326_y','selected']

        df = df[cols]
        # print(tabulate(df.head(),headers='keys',tablefmt='github'))
        result.append(df)

    return result

def saveResult(gdf4326_list, gungu, p_num, meter,ca, SAVE_PATH):
    """
        정제된 gdf4326_list(demand_gdf4326, cand_gdf4326)를 각각 csv 파일로 저장
    """
    filenames = ['수요충족', '선택된후보지']
    filenames = [f'../{SAVE_PATH}/{ca}/결과값/{gungu}/{meter}/{gungu}_{p_num}개_{meter}_{name}.csv' for name in filenames]

    for df, path in zip(gdf4326_list, filenames):
        print(tabulate(df.head(), headers='keys', tablefmt='github'))
        df.to_csv(path, index=False)
        print(f"저장 완료: {path}")

if __name__ == '__main__':

    SAVE_PATH = Path('./MCLP_유동인구/')
    DEMAND_DIR_PATH = Path('../모델 동작/수요지점')
    CAND_DIR_PATH = Path('../모델 동작/입지후보지')

    # 커버리지 반경 (단위: m)
    coverage_radius = 210

    # 쓰레기통 개수 리스트 (5배수)
    p_num_list = [10, 15, 20, 25]


    # 시군구 목록
    # gungu_list = ['남구','달서구','동구','북구','서구','수성구','중구']
    gungu_list = ['북구','수성구']
    # 사용할 커버리지 반경 폴더
    meter = f'{coverage_radius}m'

    # 사용할 가중치 파일
    category = '5186_pca_대구가중치 적용'

    WEIGHT=True
    ca='가중치있음'

    for p_num in p_num_list:
        print(f'쓰레기통 개수: {p_num}개')
        # 쓰레기통 개수
        # p_num = 10

        for gungu in gungu_list:
            print(f'{gungu} mclp 문제 풀기 시작')
            start_time = time.time() # 시작 시간 기록

            # 후보지점 파일 읽기
            for cand_file in (CAND_DIR_PATH/meter).glob("*.csv"):
                if cand_file.name.startswith(gungu):
                    cand_df = pd.read_csv(cand_file,index_col=0)
                    print(cand_file.name,': 입지후보지 데이터 프레임')
                    print(tabulate(cand_df.head(), headers='keys',tablefmt='github'))

            # 수요지점 파일 읽기
            for demand_file in (DEMAND_DIR_PATH/gungu/f'유동인구').glob('*.csv'):
                if (category in demand_file.name):
                    print(f'{demand_file.name}: 수요지점 데이터프레임')
                    demand_df = pd.read_csv(demand_file,index_col=0)
                    print(tabulate(demand_df.head(), headers='keys',tablefmt='github'))

            # mclp 문제 계산 및 시각화
            demand_df, cand_df, selected_cands, covered_demand = calMclp(demand_df, cand_df,p_num,coverage_radius,WEIGHT)
            demand_gdf, cand_gdf = makeGeodf(demand_df,cand_df,selected_cands,covered_demand)
            gdf4326_list = drawMap(demand_gdf,cand_gdf,coverage_radius, gungu, p_num, meter, SAVE_PATH, ca)

            # 결과값들 저장하기
            gdf4326_list = getWgs(gdf4326_list)
            saveResult(gdf4326_list,gungu,p_num,meter,ca,SAVE_PATH)

            # 종료 시간 및 경과 시간 계산
            end_time = time.time()
            elapsed_time = end_time - start_time
            min = int(elapsed_time // 60) # 180초 // 60 = 0(초)
            sec = int(elapsed_time % 60) # 180초 % 60 = 3(분)
            print(f" {gungu} mclp 문제 풀이 완료 — 소요 시간: {min}분 {sec}초")
            print('-'*100)

    # cov = compute_coverage_matrix(demand_df,cand_df,coverage_radius)
    # demand_df, cand_df, selected_cands, covered_demand = calMclp(demand_df, cand_df,p_num,coverage_radius)
    # demand_gdf, cand_gdf = makeGeodf(demand_df,cand_df,selected_cands,covered_demand)
    # drawMap(demand_gdf,cand_gdf,coverage_radius, SAVE_PATH)
