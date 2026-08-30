function params = SystemParams()
    %% 系统级参数
    params.sys = struct(...
        'fc',            77e9,        ... % 载波频率77GHz
        'BW',            300e6,       ... % 带宽300MHz
        'NumSubcarriers', 128,         ... % OFDM子载波数
        'Nt',            4,           ... % 发射天线
        'Nr',            8,           ... % 接收天线
        'ModOrder',      4            ... % QPSK调制
    );
    
    %% CDL信道参数 (3GPP TR 38.901)
    params.channel = struct(...
        'DelayProfile',    'CDL-D',    ... % 城市宏小区场景
        'DelaySpread',     100e-9,     ... % 时延扩展100ns
        'AngleScaling',    true,       ...
        'MaxDopplerShift', 500,        ... % 最大多普勒频移500Hz
        'NumPaths',        6           ...
    );
    
    %% 算法参数
    params.algo = struct(...
        'PilotInterval',   4,          ... % 导频间隔
        'CS_Sparsity',     4,          ... % 压缩感知稀疏度
        'DL_HiddenUnits',  [64,32],    ... % 神经网络隐藏层
        'TrainingEpochs',  50          ...
    );
    
    %% 路径配置
    params.path = struct(...
        'DataDir',      'Data/',      ...
        'ModelDir',     'Models/',    ...
        'ResultDir',    'Results/'    ...
    );
end