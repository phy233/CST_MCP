function deleteResult(mws)
%DELETERESULT 删除当前工程下的结果

%warning('当前工程的所有结果将被删除');
mws.invoke('DeleteResults');

end

