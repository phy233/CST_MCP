function is_exist = check_material_exists(mws, material_name)
% 检查材料是否存在
%
material_name = ensure_cst_string(material_name);
% 直接调用接口，不走VBA
tmp = invoke(mws,'Material');
is_exist = tmp.invoke('Exists',material_name);

release(tmp);
end