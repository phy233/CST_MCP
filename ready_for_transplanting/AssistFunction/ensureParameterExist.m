function Isexist = ensureParameterExist(mws,paraName)
%ENSUREPARAMETEREXIST 获取参数是否存在

paraName = ensure_cst_string(paraName);
Isexist = mws.invoke('DoesParameterExist',paraName);

end

