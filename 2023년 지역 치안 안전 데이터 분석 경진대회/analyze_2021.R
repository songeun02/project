install.packages("xlsx")
library(xlsx)
Sys.setenv(JAVA_HOME="C:Program Files/Java/jdk-18.0.2.1")
install.packages("rJava")
library(xlsx)
library(rJava)

# ----------------------------------------------------------------------
data2021 <- read.csv(file ='KP2021.csv',fileEncoding = "euc-kr",header = T)
data2021
View(data2021)

data2021_1 <- subset(data2021, EVT_CL_CD=='401') # 사고종류 = 교통사고 
data2021_1
View(data2021_1)
dim(data2021_1)

data2021_1_daejeon <- subset(data2021_1,NPA_CL=='13') # 경찰청구분 = 대전 
View(data2021_1_daejeon)

data2021_daejeon_excpet_HPPN_NA <- subset(data2021_1_daejeon,HPPN_Y != 'NA')
View(data2021_daejeon_excpet_HPPN_NA)

data2021_1_daejeon_map_address <-subset(data2021_daejeon_excpet_HPPN_NA,select =c(RECV_CPLT_DM,HPPN_X,HPPN_Y) ) 
data2021_1_daejeon_map_address
View(data2021_1_daejeon_map_address)

row_num <- nrow(data2021_1_daejeon_map_address)
my <- c()
for(i in 1:row_num){
  my[i] <- substr(data2021_1_daejeon_map_address$RECV_CPLT_DM[i],1,5)
}
my
View(my)
data2021_1_daejeon_map_address_0<- data.frame(data2021_1_daejeon_map_address,my)
View(data2021_1_daejeon_map_address_0)

date_2021 <- c()
for(i in 1:row_num){
  date_2021[i] <- substr(data2021_1_daejeon_map_address$RECV_CPLT_DM[i],1,8)
}
View(date_2021)
data2021_1_daejeon_map_address_0<- data.frame(data2021_1_daejeon_map_address,date_2021)
View(data2021_1_daejeon_map_address_0)

count_happen_daejeon_2021_month <- table(data2021_1_daejeon_map_address_0$my)
barplot(count_happen_daejeon_2021_month)

install.packages('ggmap')
ggmap_key <- 'AIzaSyC0KeTEeGxabXPdPUEcZZQHVMtHt7RSQiE'
library(ggmap)
register_google(ggmap_key)

# 2021 달 사고 발생 좌표 그래픽 - 갤러리아 백화점 타임월드점 확대 
data2021_1_daejeon_map_address_2021_01 <- subset(data2021_1_daejeon_map_address_0,my=='21/01')
daejeon_map1 <- get_googlemap('대전', maptype = 'roadmap', scale = 2,zoom = 13,color='bw')
daejeon_map1
ggmap(daejeon_map1) +geom_point(data = data2021_1_daejeon_map_address_2021_01, aes(x = HPPN_X, y = HPPN_Y,color=factor(date_2021)), size = 1)

# 유성호텔, 홈플러스 확대 - 대전 
data2021_1_daejeon_map_address_2021_01 <- subset(data2021_1_daejeon_map_address_0,my=='21/01')
daejeon_map1 <- get_googlemap(c(lon=127.351293,lat=36.351124), maptype = 'roadmap', scale = 2,zoom = 14,color='bw')
daejeon_map1
ggmap(daejeon_map1) +geom_point(data = data2021_1_daejeon_map_address_2021_01, aes(x = HPPN_X, y = HPPN_Y,color=factor(date_2021)), size = 1)
