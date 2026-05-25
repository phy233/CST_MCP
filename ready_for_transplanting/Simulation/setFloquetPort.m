function setFloquetPort(mws, zmin_ref_dist, zmax_ref_dist, is_circular)
% mws: CST 对象句柄
% zmin_ref_dist: Zmin 端口参考面距离 (数值或字符串, 如 "0" 或 "-lambda/4")
% zmax_ref_dist: Zmax 端口参考面距离 (数值或字符串)
% is_circular: 布尔值 (true 为圆极化, false 为线极化)

% 1. 处理极化方式的布尔值转换
if is_circular
    pol_str = 'True';
else
    pol_str = 'False';
end

% 2. 处理距离参数 (如果是数字则转为字符串，如果是字符串则直接使用)
if isnumeric(zmin_ref_dist)
    zmin_str = num2str(zmin_ref_dist);
else
    zmin_str = zmin_ref_dist;
end

if isnumeric(zmax_ref_dist)
    zmax_str = num2str(zmax_ref_dist);
else
    zmax_str = zmax_ref_dist;
end

% 3. 构造 VBA 指令
% 注意：Zmin 和 Zmax 的极化设置通常需要保持一致，这里统一切换
vba_code = sprintf([...
    'With FloquetPort \n', ...
    ' .Reset \n', ...
    ' .SetDialogTheta "0" \n', ...
    ' .SetDialogPhi "0" \n', ...
    ' .SetPolarizationIndependentOfScanAnglePhi "0.0", "False" \n', ...
    ' .SetSortCode "+beta/pw" \n', ...
    ' .SetCustomizedListFlag "False" \n', ...
    ' \n', ...
    ' .Port "Zmin" \n', ...
    ' .SetNumberOfModesConsidered "2" \n', ...
    ' .SetDistanceToReferencePlane "%s" \n', ...      % 动态填入 Zmin 距离
    ' .SetUseCircularPolarization "%s" \n', ...       % 动态填入极化
    ' \n', ...
    ' .Port "Zmax" \n', ...
    ' .SetNumberOfModesConsidered "2" \n', ...
    ' .SetDistanceToReferencePlane "%s" \n', ...      % 动态填入 Zmax 距离
    ' .SetUseCircularPolarization "%s" \n', ...       % 动态填入极化
    'End With'], ...
    zmin_str, pol_str, zmax_str, pol_str);

sCommand = [vba_code 10];
sCommand = [sCommand 10 'MakeSureParameterExists "theta", "0"'];
sCommand = [sCommand 10 'SetParameterDescription "theta", "spherical angle of incident plane wave"'];
sCommand = [sCommand 10 'MakeSureParameterExists "phi", "0"'];
sCommand = [sCommand 10 'SetParameterDescription "phi", "spherical angle of incident plane wave"'];
% 4. 发送指令
mws.invoke('AddToHistory', 'Set Floquet Advanced', sCommand);
end
