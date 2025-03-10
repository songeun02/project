install.packages("xlsx")
library(xlsx)
Sys.setenv(JAVA_HOME="C:Program Files/Java/jdk-18.0.2.1")
install.packages("rJava")
library(xlsx)
library(rJava)

# ----------------------------------------------------------------------
data2020 <- read.csv(file ='NPA2020.csv',fileEncoding = "euc-kr",header = T)
data2020
View(data2020)

data_happen <- subset(data2020, EVT_CL_CD=='401') # 사고종류 = 교통사고 (공통)
data_happen
View(data_happen)
dim(data_happen)

# 경찰청구분 = 대전 
data1_daejeon <- subset(data_happen,NPA_CL=='13'& substr(HPPN_OLD_ADDR,1,2)=='대전') 
View(data1_daejeon)

# 각 지역별 교통사고량 확인
row_num1 <- nrow(data2020)
daejeon_count <- 0
sejong_count <- 0
chungnam_count <- 0
for(i in 1:row_num1){
  if(substr(data2020$HPPN_OLD_ADDR[i],1,2)=='대전'){
    daejeon_count <- daejeon_count+1
  } else if (substr(data2020$HPPN_OLD_ADDR[i],1,2)=='세종'){
    sejong_count <- sejong_count+1
  }else if (substr(data2020$HPPN_OLD_ADDR[i],1,2)=='충청'){
    chungnam_count <- chungnam_count+1
  }
}

happen_count <- c(daejeon_count,sejong_count,chungnam_count)
happen_count

# 충남은 지역이 너무 커서 교통 사고량이 많다고 판단.
# 대전은 충남보다 훨씬 작지만 세종과는 비슷하다고 판단.
# 세종과 비슷한 지역 넓이지만 교통 사고량이 많이 차이 나서 대전 분석 진행 
data1_daejeon_excpet_HPPN_0 <- subset(data1_daejeon,HPPN_Y != '0')  

data1_daejeon_map_address <-subset(data1_daejeon_excpet_HPPN_0,select =c(RECV_CPLT_DT,HPPN_X,HPPN_Y) ) 
data1_daejeon_map_address
View(data1_daejeon_map_address)

row_num <- nrow(data1_daejeon_map_address)
my_daejeon_2020 <- c()
for(i in 1:row_num){
  # 년도와 월 추출 
  my_daejeon_2020[i] <- substr(data1_daejeon_map_address$RECV_CPLT_DT[i],1,6)
}  

data1_daejeon_map_address_0<- data.frame(data1_daejeon_map_address,my_daejeon_2020) 
View(data1_daejeon_map_address_0) 

count_happen_daejeon_2020_month <- table(data1_daejeon_map_address_0$my)
count_happen_daejeon_2020_month
month_plot = barplot(count_happen_daejeon_2020_month, names=c("1월","2월","3월","4월","5월","6월","7월","8월","9월","10월","11월"),ylim=c(0,3500), main="2020년 월별 교통사고량")
# 그래프에 값 출력
text(x=month_plot, y=count_happen_daejeon_2020_month,labels=count_happen_daejeon_2020_month,pos=3,col="black")

# 달마다 발생하는 교통사고 평균 수 
mean(count_happen_daejeon_2020_month)
count_happen_daejeon_2020_month - mean(count_happen_daejeon_2020_month)

# 구글맵 시각화 
install.packages('ggmap')
ggmap_key <- 'AIzaSyC0KeTEeGxabXPdPUEcZZQHVMtHt7RSQiE'
library(ggmap)
register_google(ggmap_key)

# 2020 대전 하루 사고 발생 좌표 그래픽 - 갤러리아 백화점 타임월드점 확대 
data1_daejeon_map_address_2020_01_01 <- subset(data1_daejeon_map_address_0,RECV_CPLT_DT=='20200101')

daejeon_map1 <- get_googlemap('대전', maptype = 'roadmap', scale = 2,zoom = 13,color='bw')
daejeon_map1
ggmap(daejeon_map1) +geom_point(data = data1_daejeon_map_address_2020_01_01, aes(x = HPPN_X, y = HPPN_Y), size = 1,color='red')

# 2020 달 사고 발생 좌표 그래픽 - 갤러리아 백화점 타임월드점 확대 
data1_daejeon_map_address_2020_01 <- subset(data1_daejeon_map_address_0,my_daejeon_2020=='202001')

daejeon_map1 <- get_googlemap('대전', maptype = 'roadmap', scale = 2,zoom = 13,color='bw')
daejeon_map1
ggmap(daejeon_map1) +geom_point(data = data1_daejeon_map_address_2020_01, aes(x = HPPN_X, y = HPPN_Y,color=factor(RECV_CPLT_DT)), size = 1)

# 유성호텔, 홈플러스 확대 - 대전 
data1_daejeon_map_address_2020_01 <- subset(data1_daejeon_map_address_0,my_daejeon_2020=='202002')

daejeon_map1 <- get_googlemap(c(lon=127.351293,lat=36.351124), maptype = 'roadmap', scale = 2,zoom = 14,color='bw')
daejeon_map1
ggmap(daejeon_map1) +geom_point(data = data1_daejeon_map_address_2020_01, aes(x = HPPN_X, y = HPPN_Y,color=factor(RECV_CPLT_DT)), size = 1)
