data GDP_YoY;
infile '/home/u63897494/sasuser.v94/실질GDP(전년동기비).txt';
input period $ gdp;
gdp_log = log(gdp);
/* 1차 차분 */
dif_gdp_log = dif(gdp_log);

year = input(scan(period,1,'/'),4.);
quarter = input(substr(scan(period,1,'/'),5),1.);
year_qtr = year + (quarter-1)/4;
run;

proc sgplot data=GDP_YoY;
series x=year_qtr y=gdp; 
/* 2000년부터 5년 단위로 지정 */
/* xaxis values=(2000 to 2025 by 5) label="time"; */
xaxis values=(2000 to 2025 by 1) label="time";
yaxis label="GDP";
run;

proc arima;
identify var=gdp_log nlag=18;
/* AR(1) 적합 */
estimate p=1 method=ml; run;
forecast lead=10 out=fore id=gdp;
run;

/* fore 데이터셋 확인 */
proc print data=fore;
run;

proc arima;
identify var=residual; run;

data fore; 
set fore; time=_n_; run;

data fore;
set fore;
  	if time >= 1 and time <= 95 then FORECAST = .;
  	if time > 95 then gdp = .;
  	GDP_Pred = exp(forecast);
	L95_Pred = exp(l95);           
  	U95_Pred = exp(u95); 
run;

/* fore 데이터셋 확인 */
proc print data=fore;
run;


proc sgplot;
series x=time y=gdp / markers;
xaxis label="time"; yaxis label="GDP";
series x=time y=GDP_Pred / markers; 
run;
