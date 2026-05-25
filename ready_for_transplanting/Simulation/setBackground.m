function setBackground(mws,XminSpace,XmaxSpace,YminSpace,YmaxSpace,ZminSpace,ZmaxSpace)
%SETBACKGROUND 设定仿真背景
%

sCommand = '';
sCommand = [sCommand 'With Background' ];
sCommand = [sCommand 10 '.ResetBackground'];
sCommand = [sCommand 10 '.Type "Normal"' ];
sCommand = [sCommand 10 sprintf('.XminSpace "%.2f"',XminSpace)];
sCommand = [sCommand 10 sprintf('.XmaxSpace "%.2f"',XmaxSpace)];
sCommand = [sCommand 10 sprintf('.YminSpace "%.2f"',YminSpace)];
sCommand = [sCommand 10 sprintf('.YmaxSpace "%.2f"',YmaxSpace)];
sCommand = [sCommand 10 sprintf('.ZminSpace "%.2f"',ZminSpace)];
sCommand = [sCommand 10 sprintf('.ZmaxSpace "%.2f"',ZmaxSpace)];
sCommand = [sCommand 10 '.ApplyInAllDirections "False"'];

sCommand = [sCommand 10 'End With'] ;
invoke(mws, 'AddToHistory','define background', sCommand);
end

