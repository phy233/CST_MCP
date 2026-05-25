function  defaultUnitInitialize(mws)
% 初始化为默认单位
%
sCommand = '';
sCommand = [sCommand 'With Units' ];
sCommand = [sCommand 10 '.Geometry "mm"'];
sCommand = [sCommand 10 '.Frequency "ghz"' ];
sCommand = [sCommand 10 '.Voltage "V"' ];
sCommand = [sCommand 10 '.Resistance "Ohm"' ];
sCommand = [sCommand 10 '.Inductance "nH"' ];
sCommand = [sCommand 10 '.Time "ns"'];
sCommand = [sCommand 10 '.Current "A"'];
sCommand = [sCommand 10 '.Conductance "Siemens"'];
sCommand = [sCommand 10 '.Capacitance "pF"'];
sCommand = [sCommand 10 'End With'] ;
invoke(mws, 'AddToHistory','define units', sCommand);
end

