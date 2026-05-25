function setFrequencySolver(mws,portInfo)
%SETFREQUENCYSOLVER 设定频域求解器，只设定端口，其他一概为默认

%% 1. 提取 Port 信息
    if isfield(portInfo, 'port')
        rawPort = portInfo.port;
    elseif isfield(portInfo, 'Port')
        rawPort = portInfo.Port;
    else
        error('Error: portInfo 结构体中缺少 "port" 或 "Port" 字段。');
    end

    %% 2. 提取 Mode 信息 (默认为 1)
    if isfield(portInfo, 'mode')
        rawMode = portInfo.mode;
    elseif isfield(portInfo, 'Mode')
        rawMode = portInfo.Mode;
    else
        rawMode = 1; % 缺省值
    end

    %% 3. 数据清洗与规则校验 (根据文档要求)
    
    % 预处理 Port：转为字符以便判断
    if isnumeric(rawPort)
        isPortNum = true;
    else
        isPortNum = false;
        strPort = char(rawPort);
    end

    % 规则 A: "Plane Wave" -> mode 必须为 "1"
    if ~isPortNum && strcmpi(strPort, 'Plane Wave')
        rawMode = 1; 
        % 可以在这里打印提示，或保持静默
    end

    % 规则 B: "List" -> mode 必须为 "List"
    if ~isPortNum && strcmpi(strPort, 'List')
        rawMode = 'List';
    end

    %% 4. 格式化为 VBA 字符串
    % CST VBA 语法要求：如果是枚举字符串，必须加双引号；如果是数字，直接写数字。

    % --- 处理 Port ---
    if isnumeric(rawPort)
        % 情况: int port
        valPortStr = num2str(rawPort);
    else
        % 情况: enum "All", "Plane Wave", etc.
        valPortStr = sprintf('"%s"', char(rawPort));
    end

    % --- 处理 Mode ---
    if isnumeric(rawMode)
        % 情况: int mode
        valModeStr = num2str(rawMode);
    else
        % 情况: enum "List", "All", etc.
        valModeStr = sprintf('"%s"', char(rawMode));
    end

% 1. 构造标准的 VBA 字符串
% 注意：valPortStr 和 valModeStr 应该是上一轮代码中处理好的字符串
% 例如: valPortStr 是 "1" (数字) 或 ""Plane Wave"" (带引号的字符串)
vba_cmd = 'FDSolver.Reset';
vba_cmd = [vba_cmd 10 sprintf('FDSolver.Stimulation %s, %s', valPortStr, valModeStr)];

% 2. 通过 AddToHistory 发送
% 这样不仅执行了设置，还会在 CST 左侧 History List 中留存记录，保证模型参数化稳定性
mws.invoke('AddToHistory', 'Define Stimulation Source', vba_cmd);

end

