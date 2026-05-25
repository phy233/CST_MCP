function quitCSTproj(mws)
% 退出CST

mws.invoke('quit');
release(mws);

end