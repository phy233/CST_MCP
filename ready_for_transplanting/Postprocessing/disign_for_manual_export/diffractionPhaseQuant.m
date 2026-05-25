% function [M_quantized,M_quantizedLabel] = diffractionPhaseQuant(M,levels)
% %DIFFRACTIONPHASEQUANT 对衍射层训练结果进行量化
% 
% % for i=1:numel(M)
% %     M{i}=angle(M{i});
% % end
% M=angle(M);
% 
% % 计算量化步长
% % levels个级别意味着有levels个量化值
% % 从-π到π总共2π的范围，需要levels-1个间隔
% step = 2*pi / (levels - 1);
% 
% % 生成量化级别（从-π到π的均匀分布）
% quant_levels = linspace(-pi, pi, levels);
% 
% % 初始化量化后的元胞数组
% %     M_quantized = cell(size(M));
% %     M_quantizedLabel = cell(size(M));
% 
% % 遍历元胞数组中的每个矩阵
% %     for i = 1:numel(M)
% % 获取当前矩阵
% %         current_matrix = M{i};
% current_matrix = M;
% % 对矩阵中的每个元素进行量化
% quantized_matrix = zeros(size(current_matrix));
% quantized_label = zeros(size(current_matrix));
% 
% % 使用最近的量化级别
% % 计算每个元素距离哪个量化级别最近
% for k = 1:numel(current_matrix)
%     % 计算当前值与所有量化级别的距离
%     [~, idx] = min(abs(current_matrix(k) - quant_levels));
%     quantized_matrix(k) = quant_levels(idx);
%     quantized_label(k) = idx;
% end
% 
% 
% % 将量化后的矩阵存入新的元胞数组
% %         M_quantized{i} = quantized_matrix;
% %         M_quantizedLabel{i} = quantized_label;
% M_quantized= quantized_matrix;
% M_quantizedLabel= quantized_label;
% 
% %     end
% end
% 



% function [M_quantized_rad, labels] = diffractionPhaseQuant(M, levels)
% % DIFFRACTIONPHASEQUANT D2NN标准相位量化 (均匀量化)
% % 输入:
% %   M: 复数矩阵 或 相位矩阵
% %   bits: 量化位数 (如 1, 2, 3, 4...)
% % 输出:
% %   M_quantized_rad: 量化后的离散相位值 (弧度)
% %   labels: 对应的整数索引 (0 ~ 2^bits-1)
% 
% 
%     % 1. 提取相位
%     if ~isreal(M)
%         phi = angle(M);
%     else
%         phi = M;
%     end
% 
%     % 2. 映射到 [0, 2pi) 区间 (处理周期性)
%     % 这一步解决了 -pi 和 pi 的问题，它们都会变成 0 (或接近 2pi)
%     phi = mod(phi, 2*pi);
% 
%     % 3. 归一化并取整 (核心逻辑)
%     % 将 [0, 2pi) 映射到 [0, levels) 连续区间
%     phi_norm = phi / (2*pi) * levels;
%     
%     % 向下取整得到索引 [0, 1, ..., levels-1]
%     labels = floor(phi_norm);
%     
%     % 4. 边界保护
%     % 极少数情况下 mod 可能会保留 2pi (浮点误差)，导致 labels=levels
%     % 强制将其归入最后一个状态
%     labels(labels >= levels) = levels - 1;
% 
%     % 5. 映射回离散相位值 (取区间左端点或中心)
%     % 这里采用标准的等间隔分布: 0, d, 2d, ...
%     step = 2*pi / levels;
%     M_quantized_rad = labels * step;
% 
%     % (可选) 为了美观，可以把大于 pi 的值映回 [-pi, pi)
%     % 这不影响物理结果，因为 exp(j*3/2*pi) == exp(-j*pi/2)
% %     M_quantized_rad(M_quantized_rad > pi) = M_quantized_rad(M_quantized_rad > pi) - 2*pi;
% end

function [M_quantized_rad, labels] = diffractionPhaseQuant(M, levels)
% DIFFRACTIONPHASEQUANT D2NN标准相位量化 (修正版: Round 四舍五入)
% 输入:
%   M: 复数矩阵 或 相位矩阵
%   levels: 量化层级数 (例如 2bit -> 4)
% 输出:
%   M_quantized_rad: 量化后的离散相位值 (弧度)
%   labels: 对应的整数索引 (0 ~ levels-1)

    % 1. 提取相位
    if ~isreal(M)
        phi = angle(M);
    else
        phi = M;
    end

    % 2. 映射到 [0, 2pi) 区间 (处理周期性)
    % 这一步保证所有相位都是正数，便于计算
    phi = mod(phi, 2*pi);

    % 3. 归一化并四舍五入 (核心逻辑修改)
    % 原逻辑: floor(phi / (2*pi) * levels) -> 有偏 (Systematic Bias)
    % 新逻辑: round(phi / (2*pi) * levels) -> 无偏 (Nearest Neighbor)
    
    phi_norm = phi / (2*pi) * levels;
    
    % 使用 round 进行四舍五入
    idx = round(phi_norm);
    
    % 4. 周期性边界处理 (关键步骤)
    % 情况A: 0.1pi -> idx = 0
    % 情况B: 1.9pi -> idx = levels (例如4)
    % 因为 2pi 和 0 是等价的，所以 idx=levels 必须映射回 0
    labels = mod(idx, levels);

    % 5. 映射回离散相位值
    step = 2*pi / levels;
    M_quantized_rad = labels * step;

end
