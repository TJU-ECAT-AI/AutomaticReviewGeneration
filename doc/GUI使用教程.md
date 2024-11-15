<h1 align="center">
图形化界面使用教程
</h1>

# 一、准备API密钥（该步骤下述教程来自GPT4）
>
>  GUI运行许可证在本仓库根文件夹的[License文件](https://github.com/Invalid-Null/AutomaticReviewGeneration/raw/main/License)，和exe文件放在同个文件夹下即可。请勿修改License文件的文件名。
> 
> 准备API密钥是使用各种API服务的前提。本指南涵盖了如何获取SerpAPI、LLM以及Elsevier的API密钥。
> 
> #### SerpAPI密钥
> 
> 1. **注册或登录**
>    - 访问 [SerpAPI](https://serpapi.com/) 网站，注册一个账户或者如果你已经有账户则登录。
> 2. **访问仪表盘**
>    - 登录后，导航到你的用户仪表盘。
> 3. **查找或生成API密钥**
>    - 在仪表盘上，你应该能够看到你的API密钥。如果没有，可能会有选项让你生成一个新的密钥。
> 4. **复制API密钥**
>    - 复制API密钥以便在你的应用程序中使用。
> 
> #### LLM密钥（支持Claude API和OpenAI格式的API）
> 
> 1. **注册或登录**
>    - 确定LLM（大型语言模型）API提供商（如OpenAI），创建账户或登录。
> 2. **获取API访问权限**
>    - 转到网站的API或开发者部分。
> 3. **生成API密钥**
>    - 寻找生成新API密钥的选项，并按照提示创建一个。
> 4. **复制并保护密钥**
>    - 复制生成的API密钥，并将其安全存储，因为它允许访问LLM服务。
> 
> #### Elsevier密钥
> 
> 1. **Elsevier账户**
>    - 访问 [Elsevier的开发者门户](https://dev.elsevier.com/)，注册或登录。
> 2. **创建新的API密钥**
>    - 导航到可以创建或管理API密钥的部分。这可能在你的账户设置或一个特定的“API密钥”部分。
> 3. **应用详情**
>    - 你可能需要提供关于你的应用的详情，包括其名称和用途，以生成API密钥。
> 4. **获取并存储密钥**
>    - 提交后，你的API密钥将被显示。复制这个密钥，并将其安全地保存。
> 
> #### 通用提示
> 
> - **安全**：保持你的API密钥的机密性，以防止未经授权的访问。
> - **再生产**：如果密钥被泄露，尽快从服务的仪表盘重新生成它。
> - **使用限制**：了解与你的API密钥相关的任何使用限制或配额，以避免服务中断。

# 二、下载预打包的exe文件并运行（该步骤下述教程来自GPT4）
> 
> 以下步骤将指导你如何从指定的GitHub页面下载并运行exe文件。
> 
> #### 步骤
> 
> 1. **访问GitHub发布页面**
>    - 打开浏览器，访问 [AutomaticReviewGeneration的发布页面](https://github.com/Invalid-Null/AutomaticReviewGeneration/releases)。
> 2. **选择版本**
>    - 浏览不同的发布版本，选择你需要下载的版本。
> 3. **下载exe文件**
>    - 在选定的版本中，找到以`.exe`结尾的文件。点击文件名旁边的下载链接进行下载。
> 4. **运行exe文件**
>    - 下载完成后，找到下载的`.exe`文件，双击运行。
>    - 如果系统提示“未知的发布者”，选择“运行”以继续。
> 5. **警告：并非所有电脑系统都会兼容此程序，如果发生兼容性问题，你需要下载Python源代码，并且按照说明文件正确安装所有依赖库，已运行该程序**

# 三、界面按钮介绍
>  **打开程序后界面如下**
>  [![启动界面](0.png)](https://raw.githubusercontent.com/Invalid-Null/AutomaticReviewGeneration/main/doc/0.png)
> 
>  - TOPIC：生成的综述主题
>  - Demo：是否以少量文献进行生成测试
>  - Whole Process：是否全流程进行，还是只进行文献检索和下载
>
> <!-- -->   
>
>  - Skip Literature Search：是否跳过文献检索模块，进行后续的步骤
>  - Skip Topic Formulation：是否跳过主题生成模块，进行后续的步骤
>  - Skip Knowledge Extraction：是否跳过知识提取模块，进行后续的步骤
>  - Skip Review Composition：是否跳过综述生成模块，进行后续的步骤
>
> <!-- -->   
>
>  - Search Options：打开文献检索选项对话框
>  - LLM Options：打开大语言模型选项对话框
>  - Review Options：打开综述评定选项对话框
>
> <!-- -->   
>
>  - Show/Hide Options：是否折叠配置选项
>  - Run Automatic Review Generation：开始综述生成
> 
> **折叠配置选项后界面如下**
>  [![折叠选项界面](1.png)](https://raw.githubusercontent.com/Invalid-Null/AutomaticReviewGeneration/main/doc/1.png)

# 四、文献检索选项配置
>  1. 文献检索选项配置对话框
>  
>  **打开文献检索选项配置对话框界面如下**
>  [![文献检索选项配置对话框](2.png)](https://raw.githubusercontent.com/Invalid-Null/AutomaticReviewGeneration/main/doc/2.png)
> 
>  - Custom Journals：打开自定义文献列表，软件将仅检索用户自定义的文献，如果想重置文献列表，请删除所有自定义文献
>  - Add to Serp API List：打开Serp API密钥（列表）配置对话框
>  - Add to Research Keys：打开检索关键词（列表）配置对话框，即使用该关键词（列表）进行文献检索
>  - Add to Screen Keys：打开过滤关键词（列表）配置对话框，即使用该关键词（列表）进行标题和摘要的过滤
>  - Set Elsevier API Keys：设置Elsevier API密钥，用于期刊种类判断
> <!-- -->   
>
>  - StartYear：文献检索起始年份
>  - EndYear：文献检索结束年份
>  - Q1：是否在2022年中科院分区表化学/化工期刊中的一区期刊中检索
>  - Q2&Q3：是否在2022年中科院分区表化学/化工期刊中的二三区期刊中检索
>
> <!-- -->   
>
>  - Save：保存文献检索配置
>
>  2. Serp API密钥（列表）配置对话框
>  
>  **打开Serp API密钥（列表）配置对话框界面如下**
>  [![Serp API密钥（列表）配置对话框](3.png)](https://raw.githubusercontent.com/Invalid-Null/AutomaticReviewGeneration/main/doc/3.png)
>
>  输入前述步骤中获得的Serp API密钥，一次一个，不含引号，输入后点击`OK`。
>
>  直接点击`OK`或点击`Cancel`不修改Serp API密钥配置。
>  
>  输入`!!!~~~!!!`清空原有Serp API密钥配置，不含引号。
> 
>  检索关键词（列表）配置对话框和过滤关键词（列表）配置对话框与Serp API密钥（列表）配置对话框操作完全一致
> 
> 3. 点击保存，关闭文献检索选项配置对话框
>  
>  **点击保存后程序界面如下**
>  [![文献检索选项配置结果输出](4.png)](https://raw.githubusercontent.com/Invalid-Null/AutomaticReviewGeneration/main/doc/4.png)
>  
>  除了Serp API密钥（列表）之外，其他选项内容均会打印在界面上
>  
>  若配置错误，重新打开文献检索选项配置对话框进行配置
>
>  直接关闭文献检索选项配置对话框将不会保存文献检索配置选项
 
# 五、大语言模型选项配置
>  1. 大语言模型选项配置对话框
>  
>  **打开大语言模型选项配置对话框界面如下**
>  [![大语言模型选项配置对话框](5.png)](https://raw.githubusercontent.com/Invalid-Null/AutomaticReviewGeneration/main/doc/5.png)
> 
>  - Add to Claude Api Key List：打开Claude API密钥（列表）配置对话框
>  - Add to OpenAI-compatible API Url List：打开OpenAI格式API的网址（列表）配置对话框
>  - Add to OpenAI-compatible API Key List：打开OpenAI格式API的密钥（列表）配置对话框
>  - Check LLM Response：检查配置的大语言模型是否能正常访问
>
>  2. 关闭大语言模型选项配置对话框
>
>  **点击保存后程序界面如下**
>  [![大语言模型选项配置结果输出](6.png)](https://raw.githubusercontent.com/Invalid-Null/AutomaticReviewGeneration/main/doc/6.png)
>
>  上述配置对话框与Serp API密钥（列表）配置对话框操作完全一致
>
>  注意OpenAI格式API的网址和密钥需一一对应
>
>  支持添加多个类型的密钥，并能多进程访问加速
>
>  配置对话框点击确认后直接保存
>
>  关闭大语言模型选项配置对话框后，已配置的大语言模型数量会打印在界面上
>
>  建议配置后点击`Check LLM Response`检查配置的大语言模型是否能正常访问
>
>  **测试通过的示例如下**
>  [![大语言模型连接测试通过](7.png)](https://raw.githubusercontent.com/Invalid-Null/AutomaticReviewGeneration/main/doc/7.png)
>
>  **测试失败的示例如下**
>  [![大语言模型连接测试失败](8.png)](https://raw.githubusercontent.com/Invalid-Null/AutomaticReviewGeneration/main/doc/8.png)
>  根据返回结果检查失败原因并重新配置
>
>  测试失败的大语言模型将不会被应用于综述生成过程中

# 六、综述评估选项配置
>  1. 综述评估选项配置对话框
>  
>  **打开综述评估选项配置对话框界面如下**
>  [![综述评估选项配置对话框](9.png)](https://raw.githubusercontent.com/Invalid-Null/AutomaticReviewGeneration/main/doc/9.png)
> 
>  - Skip Compare Articles：跳过文章段落对比部分
>  - Direct Topic Generation：直接生成综述主题

>  2. 关闭综述评估选项配置对话框
>
>  **点击保存后程序界面如下**
>  [![综述评估选项配置结果输出](10.png)](https://raw.githubusercontent.com/Invalid-Null/AutomaticReviewGeneration/main/doc/10.png)

# 七、运行综述生成过程
>  参考**四、界面按钮介绍**，选择运行的模块
>
>  初始运行建议不跳过任何流程
>
>  若前面的步骤未完成时进行后续流程，将会有报错提示
>
>  运行时选项会自动折叠
>
>  支持断点续跑，运行中断后重新运行即可
>
>  - **未完成文献检索过程的提示如下**
>  - [![未完成文献检索过程](11.png)](https://raw.githubusercontent.com/Invalid-Null/AutomaticReviewGeneration/main/doc/11.png)
>
>  - **未完成主题生成过程的提示如下**
>  - [![未完成主题生成过程](12.png)](https://raw.githubusercontent.com/Invalid-Null/AutomaticReviewGeneration/main/doc/12.png)
>
>  - **未完成知识提取过程的提示如下**
>  - [![未完成知识提取过程](13.png)](https://raw.githubusercontent.com/Invalid-Null/AutomaticReviewGeneration/main/doc/13.png)

# 八、停止与重新启动
>  程序运行后，综述生成按钮会自动变成终止按钮，按下之后，程序会结束所有进程然后在一段时间后重新启动，请耐心等待
>  可以通过鼠标滚轮来查看输出窗口中的历史信息
>  - **停止和重新启动界面如下**
>  - [![停止界面与按钮](14.png)](https://raw.githubusercontent.com/Invalid-Null/AutomaticReviewGeneration/main/doc/14.png)
>  - [![重新启动界面](15.png)](https://raw.githubusercontent.com/Invalid-Null/AutomaticReviewGeneration/main/doc/15.png)
