classdef unit_Cyuanhuan

    % --- 常量属性 (Constant) ---
    % 这些值在所有实例中都是一样的，不可修改
    properties(Constant)
        unitSize = [14 14 3];
        freq = 14e9;
        codeNum = 4;
    end

    % --- 普通属性 (Properties) ---
    % 这里只定义变量名，或者赋简单的初始值
    properties
        IsMultiStruct = true;
        % 标记是平移建模还是直接建模
        IsDirectModeling = true;
        % 这里只声明 codeParam 这个容器，不要在这里赋值
        codeParam
    end

    properties
        % 单元的几何参数
        a = 14;
        h = 3;
        w = 0.3;
        w_arc = 0.3;
        h_medal = 0; % 用0.018会有个缝？？？
        ra = 5.8;
        rb = 5.2;
        phib = 200;
        phia = 220;
    end

    % --- 方法 (Methods) ---
    methods
        % 构造函数：函数名必须与类名(unitParamsTest)完全一致
        % 只有在这里才能使用 'obj' 并进行逻辑运算
        function obj = unit_Cyuanhuan()
            obj.codeParam = [];
        end


        function obj = codeModeling(obj,mws, this_code, this_center, unit_name)

            if ~check_material_exists(mws,'material1')
                defineMaterial(mws,'material1',2.2,1,0.001,0,50);
            end

            % 建立单元编码的LUT (保持不变)
            %             switch this_code
            %                 case 1
            %                     obj.phib = 200;
            %                 case 2
            %                     obj.phib = 123;
            %                 case 3
            %                     obj.phib = 111;
            %                 case 4
            %                     obj.phib = 104;
            %                 case 5
            %                     obj.phib = 98;
            %                 case 6
            %                     obj.phib = 90;
            %                 case 7
            %                     obj.phib = 75;
            %                 case 8
            %                     obj.phib = 10;
            %                 otherwise
            %                     error('输入的编码数不正确，从1开始，这里是3bit');
            %             end

            switch this_code
                case 1
                    obj.phib = 200;
                case 2
                    obj.phib = 111;
                case 3
                    obj.phib = 98;
                case 4
                    obj.phib = 75;
                otherwise
                    error('输入的编码数不正确，从1开始，这里是2bit');
            end

                % =========================================================
                % 关键修改 1: 在函数最开始，一次性将 WCS 移到单元中心
                % 之后所有操作都基于这个新的 WCS (即局部原点就是单元中心)
                % =========================================================
                activateWCS(mws, [0 0 1], this_center, [1 0 0], 1);


                % =========================================================
                % 关键修改 2: 所有坐标定义全部改为“相对坐标” (Local)
                % 不要再加 this_center
                % =========================================================

                % 1. 搭建基座
                % 基座中心在局部坐标系下就是 [0,0,0]
                defineBrick(mws, 'base', unit_name, [0 0 0], obj.a, obj.a, obj.h, 'material1');

                % 2. 画圆弧
                % 圆弧所在的 Z 平面 (局部坐标)
                localArcZ = obj.h/2;
                localArcCenter = [0, 0, localArcZ];

                % 计算起始点 (局部坐标)
                % 注意：这里直接相对于 [0,0,0] 计算，完全不涉及 this_center
                localStartA = localArcCenter - [obj.ra, 0, 0];
                localStartB = localArcCenter - [obj.rb, 0, 0];

                % 调用画图 (传入局部坐标)
                defineArcBlock(mws, unit_name, 'arc_a1', 'PEC', ...
                    obj.h_medal, obj.w_arc, obj.phia/2, localArcCenter, localStartA, 'Clockwise');
                defineArcBlock(mws, unit_name, 'arc_b1', 'PEC', ...
                    obj.h_medal, obj.w_arc, obj.phib/2, localArcCenter, localStartB, 'Clockwise');
                defineArcBlock(mws, unit_name, 'arc_a2', 'PEC', ...
                    obj.h_medal, obj.w_arc, obj.phia/2, localArcCenter, localStartA, 'CounterClockwise');
                defineArcBlock(mws, unit_name, 'arc_b2', 'PEC', ...
                    obj.h_medal, obj.w_arc, obj.phib/2, localArcCenter, localStartB, 'CounterClockwise');

                % 3. 画连接杆
                % 同样使用局部坐标
                % 连接杆位置：X=-obj.ra-obj.w/2, Y=0, Z=obj.h_medal/2 (相对于圆弧平面还是基座？假设是基座表面)
                % 你的原代码里是 activateWCS 到了 currentPoint (即基座上表面)
                % 所以这里的 Z 应该是相对于基座上表面的偏移

                % 为了保险，我们继续使用当前的 WCS (基座中心)，计算出连接杆的正确位置
                % 假设连接杆放置在基座上表面 (Z = h/2)，且连接杆自身厚度中心在 h_medal/2
                brickCenterLocal = [-obj.rb-obj.w/2, 0, obj.h/2 + obj.h_medal/2];

                defineBrick(mws, 'connectMedal', unit_name, brickCenterLocal, 2*obj.w, obj.w, obj.h_medal, 'PEC');

                % 4. 拼接
                addObj(mws, unit_name, 'arc_a1', unit_name, 'arc_a2');
                addObj(mws, unit_name, 'arc_b1', unit_name, 'arc_b2');
                addObj(mws, unit_name, 'arc_a1', unit_name, 'arc_b1');

                translationObj(mws, sprintf('%s:%s', unit_name, 'arc_a1'), 0, 0, obj.h/2, 0, 1);


                addObj(mws, unit_name, 'arc_a1', unit_name, 'connectMedal');

                % 5. 复制到背面
                % 这里的平移距离是 Z 方向向下移动 h + h_medal
                translationObj(mws, sprintf('%s:%s', unit_name, 'arc_a1'), 0, 0, -obj.h-obj.h_medal, 1, 1);

                % 旋转操作
                % 此时 WCS 依然在单元中心 (基座中心)，所以直接绕局部 [0,0,0] 旋转即可
                % 不需要重新计算 currentPoint
                rotateObj(mws, unit_name, 'arc_a1_1', [0 0 0], [0 0 180], 0);

                % =========================================================
                % 恢复 WCS (可选，但为了安全建议最后重置)
                % 实际上 arrayModeling 循环开始前并没有强制重置，
                % 但因为下一轮 codeModeling 会强制 set WCS，所以这里不加也没事。
                % 不过加上是个好习惯。
                % =========================================================
                activateWCS(mws, [0 0 1], [0 0 0], [1 0 0], 0);

            end


        end
    end