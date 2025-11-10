data GDP_QoQ;

infile '/home/u63897494/sasuser.v94/실질GDP(전분기비).txt';
input period $ gdp;
year = input(scan(period,1,'.'),4.);
quarter = input(scan(scan(period,2,'.'),1,'/'),1.);
year_qtr = year + (quarter-1)/4;
run;

proc sgplot data=GDP_QoQ;
series x=year_qtr y=gdp; 
xaxis values=(2000 to 2025 by 5) label="time"; 
yaxis label="GDP";
run;

proc arima;
identify var=gdp nlag=24; run;
