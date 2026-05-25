function [S_Mag, S_Phase, S_Re, S_Im] = getSParamAtFreq(freqArr, reArr, imArr, targetFreq)
%GETSPARAMATFREQ 获取指定频点的S参数（自动插值）
%   输入:
%     mws        - CST 对象句柄
%     targetName - S参数名称 (如 'S1,1' 或 'Zmax(1)')
%     targetFreq - 目标频率 (单位需与CST设置一致，通常是 GHz)
%
%   输出:
%     S_Mag   - 幅度 (线性值，非dB)
%     S_Phase - 相位 (角度制 Deg)
%     S_Re    - 实部
%     S_Im    - 虚部

    % 1. 调用你写好的底层读取函数获取全频段数据
    %[freqArr, reArr, imArr] = smartReadSParameter(mws, targetName);

    % 2. 检查频率范围防止越界
    if targetFreq < min(freqArr) || targetFreq > max(freqArr)
        error('目标频率 %.2f 超出了当前结果的频率范围 [%.2f, %.2f]。', ...
            targetFreq, min(freqArr), max(freqArr));
    end

    % 3. 使用线性插值获取目标频点的实部和虚部
    % interp1 比 find(abs(f-ft)<tol) 更科学，精度更高
    S_Re = interp1(freqArr, reArr, targetFreq, 'linear');
    S_Im = interp1(freqArr, imArr, targetFreq, 'linear');

    % 4. 转换幅度与相位
    % 构造复数
    c_val = complex(S_Re, S_Im);
    
    % 幅度 (Linear Magnitude)
    S_Mag = abs(c_val);
    
    % 相位 (Phase in Degrees)
    % angle 计算出来是弧度 (-pi 到 pi)，转为角度
    S_Phase = rad2deg(angle(c_val));
end