function addToHistory(mws,discription,commend)
%ADDTOHISTORY 此处显示有关此函数的摘要
%   

discription = ensure_cst_string(discription);

mws.invoke('AddToHistory',discription,commend);

end

