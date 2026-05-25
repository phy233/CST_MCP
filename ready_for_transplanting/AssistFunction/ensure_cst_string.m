function str_out = ensure_cst_string(var_in)
    % var_in: 输入变量 (可能是 char, string, 或 numeric)
    % var_name_debug: 用于报错时提示变量名的字符串
    % str_out: 输出符合 CST 要求的 char 格式
    
    % 1. 判断是否为字符或字符串类型
    if ischar(var_in) || isstring(var_in)
        % 强制转换为 char (去除 MATLAB string 类的双引号属性，适应 ActiveX)
        str_out = char(var_in);
        
    % 2. 判断是否为数值类型
    elseif isnumeric(var_in)
        % 将数值转换为字符串
        % 注意：对于命名通常使用 num2str，涉及精度控制建议用 sprintf
        str_out = num2str(var_in);
        
    % 3. 异常处理：抛出错误
    else
        % 使用 error 函数中断程序，并给出清晰的提示
        error('CST_API:TypeError', ...
              '变量 "%s" 类型无效。期望：字符串或数值；实际：Class %s。', ...
              var_in, class(var_in));
    end
end