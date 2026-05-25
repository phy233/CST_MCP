close all;
clear;
clc;

data = CSTSparameterProcess('E:\seu\PNN\屎\unit\Export\data3.txt');
data_new = [data(2),data(4),data(6),data(8)];
Ismerge = 1;
IsUnwrap = 1;

figure;
CSTSPhaseDrawer(data_new,Ismerge,IsUnwrap);
legend("编码4","编码3","编码2","编码1");
figure;
CSTSAmpDrawer(data_new,Ismerge);
legend("编码4","编码3","编码2","编码1");
