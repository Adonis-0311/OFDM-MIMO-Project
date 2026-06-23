classdef ConfigLoader
    methods (Static)
        function params = LoadConfig(configFile)
            % 动态加载配置文件
            run(configFile);
            params = ValidateParams(params);  % 参数有效性检查
            
            % 创建必要目录
            if ~exist(params.path.DataDir, 'dir')
                mkdir(params.path.DataDir);
            end
        end
        
        function params = ValidateParams(params)
            % 参数验证逻辑
            assert(params.sys.NumSubcarriers > 64, ...
                '子载波数必须大于64');
            assert(ismember(params.channel.DelayProfile, {'CDL-A','CDL-D'}), ...
                '无效的信道模型配置');
        end
    end
end