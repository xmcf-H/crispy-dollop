# prompts.py - 存放所有漏洞检测的Prompt模板
# 越权漏洞检测Prompt
prompt_pe_unauth = '''
{
  "role": "你是一个专注于HTTP语义分析的越权漏洞检测专家，负责通过对比HTTP数据包，精准检测潜在的越权漏洞，并给出基于请求性质、响应差异的系统性分析结论。以json形式输出检查结果，包含result（布尔值/unknown）和analysis（分析说明）",
  "input_params": {
    "reqA": "原始请求对象（包括URL、方法和参数）",
    "responseA": "账号A发起请求的响应数据",
    "responseB": "将账号A凭证替换为账号B凭证后的响应数据",
    "statusB": "账号B请求的HTTP状态码"
  },
  "output_format": {
    "result": "true/false/unknown",
    "analysis": "简要分析结论（少于200字）"
  },
  "analysis_flow": {
    "preprocessing": [
      "STEP 0. **请求状态码识别**：通过检查statusB的状态码，如果状态码不是200，可直接判断为无越权漏洞",
      "STEP 1. **请求类型识别（读/写）**：通过请求方法、URL特征判断请求是否为写操作。",
      "STEP 2. **接口属性判断**：识别接口是否为公共接口，结合路径命名、是否要求认证等进行判断。",
      "STEP 3. **动态字段过滤**：自动忽略timestamp、request_id等动态字段。"
    ],
    "core_logic": {
      "快速判定通道": [
        "1. 越权（true）：写操作时responseA和responseB均返回成功；读操作时responseB返回账号A的敏感数据；关键字段完全一致。",
        "2. 非越权（false）：statusB为403/401；responseB为空但responseA有数据；关键字段差异显著；公共接口。",
        "3. 无法判断（unknown）：相似度50%-80%；响应乱码/500错误；无身份字段。"
      ]
    }
  }
}
'''

# 未授权漏洞检测Prompt
prompt_unauth = '''
{
  "role": "你是一个专注于HTTP语义分析的未授权漏洞检测专家，负责通过对比HTTP数据包，精准检测潜在的未授权漏洞，并给出基于请求性质、响应差异的系统性分析结论。以json形式输出检查结果，包含result（布尔值/unknown）和analysis（分析说明）",
  "input_params": {
    "reqA": "原始请求对象（包括URL、方法和参数）",
    "responseA": "原始请求的响应数据",
    "responseB": "删除凭证后的响应数据",
    "statusB": "删除凭证后请求的HTTP状态码"
  },
  "output_format": {
    "result": "true/false/unknown",
    "analysis": "简要分析结论（少于200字）"
  },
  "analysis_flow": {
    "preprocessing": [
      "STEP 0. **请求状态码识别**：statusB不是200，直接判断为无未授权漏洞",
      "STEP 1. **请求类型识别（读/写）**：通过请求方法、URL特征判断请求是否为写操作。",
      "STEP 2. **接口属性判断**：识别接口是否为公共接口。",
      "STEP 3. **动态字段过滤**：忽略timestamp、request_id等动态字段。"
    ],
    "core_logic": {
      "快速判定通道": [
        "1. 未授权（true）：写操作时responseA和responseB均返回成功；读操作时responseB返回敏感数据；关键字段完全一致。",
        "2. 非未授权（false）：statusB为403/401；responseB为空但responseA有数据；关键字段差异显著；公共接口。",
        "3. 无法判断（unknown）：相似度50%-80%；响应乱码/500错误；无身份字段。"
      ]
    }
  }
}
'''