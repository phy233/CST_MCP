classdef codingMatrixTest

    properties(Constant)
        size = [5 5];
        codeLayer = 3;
        layerDistance = [12 12 12];
        codeNum = 4;
        IsQuantized = false;
    end

    properties
        codingMatrix;
        M_quantized;
        M_quantizedLabel;
    end

    methods
        % 构造函数重构：支持多种输入方式
        %         function obj = codingMatrixTest(inputData)
        %
        %             % 情况 1: 无输入参数
        %             if nargin == 0
        %                 warning('未提供输入数据，正在生成随机测试数据...');
        %                 rng(42);
        %                 for i=1:obj.codeLayer
        %                     obj.codingMatrix{i} = randi([1, 4], obj.size);
        %                 end
        %
        %             % 情况 2: 输入为包含 M 的对象或结构体 (修正了报错行)
        %             elseif (isobject(inputData) && isprop(inputData, 'M')) || ...
        %                    (isstruct(inputData) && isfield(inputData, 'M'))
        %
        %                 fprintf('正在从模型中提取数据...\n');
        %                 obj.codingMatrix = inputData.M;
        %
        %             % 情况 3: 输入为数值矩阵
        %             elseif isnumeric(inputData)
        %                 fprintf('正在加载原始矩阵数据...\n');
        %                 obj.codingMatrix = inputData;
        %
        %             else
        %                 error('输入参数类型不支持。请传入包含M属性的模型对象、结构体或数值矩阵。');
        %             end
        %
        %             % --- 后续数据处理 ---
        %             if ~isempty(obj.codingMatrix)
        %                 [obj.M_quantized, obj.M_quantizedLabel] = diffractionPhaseQuant(obj.codingMatrix, obj.codeNum);
        %
        %                 if length(obj.M_quantized) > 2
        %                     obj.M_quantizedLabel = obj.M_quantizedLabel(2:end-1);
        %                     obj.M_quantized = obj.M_quantized(2:end-1);
        %                 end
        %             end
        %         end


        function obj = codingMatrixTest()
            warning('未提供输入数据，正在生成随机测试数据...');
            rng(42);
            for i=1:obj.codeLayer
                obj.codingMatrix{i} = randi([1, 4], obj.size);
            end
        end
    end
end