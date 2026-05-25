function startFrequencySolver(mws)
%STARTFREQUENCYSOLVER 启动频域求解器
%

tic;
tmp = invoke(mws,'FDSolver');
tmp.invoke('Start');
release(tmp);
time = toc;

disp('本轮用时%.2f秒',time);
end

