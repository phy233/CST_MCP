function startCurrentSolver(mws)
%STARTCURRENTSOLVER 开始运行当前激活的求解器

tic;
mws.invoke('RunSolver');
time = toc;
fprintf('本轮用时：%.2f\n',time);

end

