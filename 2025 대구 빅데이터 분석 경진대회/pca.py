import os
import numpy as np
import pandas as pd
from tabulate import tabulate
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from factor_analyzer.factor_analyzer import (
    calculate_kmo,
    calculate_bartlett_sphericity
)

def getDf(FILE_PATH, val, ext):
    '''
        DataFrame 만들기
    '''
    file_dict = {}
    file_list = os.listdir(FILE_PATH)
    for file in file_list:
        filename, ext_file = os.path.splitext(file)
        if (val in filename) & (ext_file == ext):
            path = os.path.join(FILE_PATH,file)
            df = pd.read_csv(path)
            file_dict[filename] = df
    return file_dict


def doPca(df, col_vars, pca_num):
    
    # 변수 선택
    scaled_df = df.copy()
    scaler = StandardScaler()
    col_vars = df[col_vars].select_dtypes(include=[np.number]).columns.tolist()
    Xs = scaler.fit_transform(df[col_vars])
    scaled_df[col_vars] = Xs
    print(Xs)
    print('\nt스케일링한 데이터프레임: ')
    print(tabulate(scaled_df,headers='keys',tablefmt='github'))

    
    # 분산 0인 변수 제거
    valid_cols_mask = Xs.std(axis=0) > 0
    Xs_valid = Xs[:, valid_cols_mask]
    col_vars_valid = np.array(col_vars)[valid_cols_mask]
    print(f"\n[ 원래 변수 수: {len(col_vars)} => 유효 변수 수: {len(col_vars_valid)} ]")
    
    # KMO 검정
    kmo_all, kmo_model = calculate_kmo(Xs_valid)
    print("\n[KMO 각 변수별 값]\n", tabulate(pd.Series(kmo_all,index=col_vars_valid).reset_index(), headers=['변수','KMO'],tablefmt='github'))
    print("KMO 전체 값:", kmo_model)

    # Bartlett의 구형성 검정 
    chi_square_value, p_value = calculate_bartlett_sphericity(Xs_valid)
    print("\n[Bartlett 구형성 검정 결과]")
    print(f"Chi-square 값: {chi_square_value}")
    print(f"p-value: {p_value}")
    if p_value < 0.05:
        print("→ p < 0.05 이므로, 상관행렬이 단위행렬이 아니며 PCA 수행 적합.")
    else:
        print("→ p ≥ 0.05 이므로, PCA 수행이 적합하지 않을 수 있음.")

    # PCA 수행
    pca = PCA(n_components=pca_num)
    scores = pca.fit_transform(Xs_valid)  # 성분점수 (n x 3)

    print("\n성분점수 (예시 5개):\n", scores[:5])
    
    loadings = pca.components_.T  # 변수별 로딩 (p x 3)
    explained_var = pca.explained_variance_
    explained_ratio = pca.explained_variance_ratio_  # [PC1_prop, PC2_prop, PC3_prop]
    cum_explained = np.cumsum(explained_ratio)
    
    # PCA 요약표
    pca_summary_df = pd.DataFrame({
        '고유값(Eigenvalue)': explained_var,
        '설명분산비율(%)': explained_ratio * 100,
        '누적 설명분산비율(%)': cum_explained * 100
    }, index=[f'PC{i+1}' for i in range(pca_num)])
    pca_summary_df['Kaiser 유지여부'] = pca_summary_df['고유값(Eigenvalue)'] > 1

    print('\n[PCA 요약표]\n')
    print(tabulate(pca_summary_df,headers='keys',tablefmt='github'))

    # Kaiser 기준 주성분 선택
    # (array([0, 1]),) -> [0] : [0,1] ->  0: PC1, 1: PC2
    choice_pca_num = np.where(pca_summary_df['고유값(Eigenvalue)'] > 1)[0]
    if len(choice_pca_num) == 0:
        choice_pca_num = [0] # 전부 1 미만이면 PC1만 사용

    print(f"\nKaiser 기준 선택 주성분: {[f'PC{i+1}' for i in choice_pca_num]}")

    # 변수별 로딩 계산
    loadings_df = pd.DataFrame(loadings, index=col_vars_valid, columns=[f'PC{i+1}' for i in range(pca_num)])
    print('\n[변수별 로딩]\n')
    print(tabulate(loadings_df,headers='keys',tablefmt='github'))
    
    # 가중치 계산
    # 예: 변수 i의 최종가중치 = loading_i_PC1 * prop1 + loading_i_PC2 * prop2
    selected_loadings = loadings[:, choice_pca_num]
    selected_ratio = explained_ratio[choice_pca_num]
    weights = np.dot(selected_loadings, selected_ratio) # 행렬곱

    # 결과 확인
    weights_sr = pd.Series(weights, index=col_vars_valid)
    print("\n[변수별 가중치]\n")
    print(tabulate(weights_sr.reset_index(),
                   headers=['변수','가중치'],
                   tablefmt='github'))

    # 변수별 가중치 곱 구하기
    weighted_values = Xs_valid * weights
    final_index = weighted_values.sum(axis=1)

    # 원본 df에 적용
    df['최종지표'] = final_index
    df_sorted = df[['군구','행정동','최종지표']].sort_values('최종지표',ascending=False)

    print('\n[읍면동 우선순위]\n')
    print(tabulate(df_sorted,headers='keys',tablefmt='github'))

    # 11. 결과 반환
    summary_dict = {
        
        '스케일링한 데이터프레임(df)': scaled_df,
        '스케일링한 값들':Xs,
        '분산이 0인 변수 제거한 데이터프레임':Xs_valid,
        '변수별 로딩값(df)' : loadings_df,
        '가중치' : weights,
        '변수별 가중치(sr)': weights_sr,
        '최종 우선순위(df)' : df_sorted
    }
    
    return summary_dict


if __name__ == '__main__':
    FILE_PATH = './모델 동작/유동인구 가중치/쓰레기통제외_버전/가중치/'
    val = '(유출인구 cctv수정본)'
    ext= '.csv'
    file_dict = getDf(FILE_PATH,val,ext)
    SAVE_PATH = './모델 동작/유동인구 가중치/쓰레기통제외_버전/최종 가중치/'
    os.makedirs(SAVE_PATH, exist_ok=True)
    
    
    # 주성분 분석 시작
    pca_dict = {}
    pca_num = 4
    
    for filename, df in file_dict.items():
        print(filename)
        col_vars = list(df.columns[2:])
        print(tabulate(df,headers='keys',tablefmt='github'))
        summary_dict = doPca(df,col_vars,pca_num)
        pca_dict[filename] = summary_dict
        print('-'*100)
    
    for key, val in pca_dict.items():
        print(val['가중치'])
        print(val['변수별 가중치(sr)'])
        break

    for filename, summary_dict in pca_dict.items():
        # 최종 우선순위
        df_sorted = summary_dict['최종 우선순위(df)']
        df_sorted.rename(columns={'최종지표':'w'}, inplace=True)
        df_sorted.to_csv(os.path.join(SAVE_PATH, f'{filename}_최종 가중치.csv'), index=False, encoding='utf-8-sig')

        print(f"[저장 완료] {filename} 결과가 {SAVE_PATH}에 저장되었습니다.")
        
