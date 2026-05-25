function M = getMFromD2NN(matAddr, IsQuant)
%GETMFROMD2NN 从训练好的d2nn模型文件中提取M

if exist(matAddr, 'file')
    data = load(matAddr, 'net');
    tmp_net = data.net;

    if IsQuant
        for k = 1:tmp_net.layerNum
            if ~isempty(tmp_net.M{k})
                % 使用 D2NN 类自带的 getQuantizedM 方法
                tmp_net = tmp_net.setM(k, tmp_net.getQuantizedM(tmp_net.M{k}));
            end
        end
    end

    M = tmp_net.M;

else
    error('模型 %s 加载失败',matAddr);


end

