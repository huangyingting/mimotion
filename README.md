# mimotion — Personal Zepp Life Automation

[![Update Steps](https://github.com/huangyingting/mimotion/actions/workflows/run.yml/badge.svg)](https://github.com/huangyingting/mimotion/actions/workflows/run.yml)

An independently maintained, private Zepp Life automation repository. There is no upstream synchronization; code and workflow changes are maintained directly here. Original project credits and the Apache-2.0 license are preserved.

The only workflow is **Update Steps**: update steps at 07:00, 15:00, and 23:00 Beijing time, or manually, then save encrypted login tokens.

## 小米运动自动刷步数（支持邮箱登录）

- 小米运动自动刷步数，小米运动APP现已改名 `Zepp Life`，为方便说明，后面还是称其为小米运动。但下载注册时请搜索 `Zepp Life`。
- 注册账号后建议先去以下网站测试自己的账号刷步数是否正常（注意这些网站只是网络上收集的，不保证安全和有效性）：
    - https://steps.hubp.de/ 提示密码错误时可以多试几次 或者切换网络
    - https://bs.yanwan.store/run4/ 验证码001或998
- 如无法刷步数同步到支付宝等，建议重新注册一个新的。

## 新注册账号使用方法

由于新注册账号没有绑定过手环，会导致华米拦截向微信同步步数，此时你需要做的就是绑定一次小米1-7代任意手环即可。如果没有可以参考以下步骤：
- 前往 `https://bs.yanwan.store/run4/` 网站执行一次步数同步
- 该网站会自动为你账号绑定一个虚拟设备（感谢该建站大佬）
- 你可以在你 Zepp Life 中看到这个虚拟的设备
- 然后按照以下步骤进行配置即可成功同步了

## Github Actions 部署指南

本仓库部署在 `master` 分支，建议使用私有仓库。账号密码只保存到 Actions 的 `CONFIG` Secret，不要提交到代码中。
当前部署的步数配置为 `MIN_STEP=15000`、`MAX_STEP=18000`。最低步数固定为15000，额外随机步数的上限按北京时间的24小时周期增长，每天午夜重置。

```text
bonus_limit = floor((MAX_STEP - MIN_STEP) × minutes_since_midnight / 1440)
steps = MIN_STEP + random_integer(0, bonus_limit)
```

例如北京时间00:00为15000，12:00随机范围为15000–16500，18:00为15000–17250，22:00为15000–17750，23:59为15000–17997。
每次执行设置当天的总步数，不累加；随机结果可能低于前一次，但始终在配置的最小和最大步数之间。

每天按北京时间07:00、15:00、23:00执行，共3次；UTC cron为 `0 7,15,23 * * *`，对应北京时间15:00、23:00及次日07:00。
仓库仅保留 `Update Steps` 工作流，不会在成功执行后自动修改计划时间。
执行中任何账号失败会使工作流失败，不再显示为成功。
Token没有变化时会跳过提交，不影响工作流成功状态。

### 一、为本仓库创建token

#### 创建小权限的限时token，推荐

- 前往[https://github.com/settings/tokens?type=beta](https://github.com/settings/tokens?type=beta)
  创建个人token，建议使用Fine-grained tokens，避免token泄露导致不必要的麻烦。
- 填写token的名称，用于自己区别干嘛用的。
- 选择token有效期，最大时长为1年。一年后需要重新续期或重建，唯一缺点
- `Repository access` 选择 `Only select repositories` 勾选 `huangyingting/mimotion`
- 点击 `Repository permissions` 展开菜单，并勾选以下四个权限即可，其他的可以不勾选
    - `Actions` Access: `Read and write` 用于获取Actions的权限
    - `Contents` Access: `Read and write` 用于更新定时任务和日志文件的权限
    - `Metadata` Access: `Read-only` 这个自带的必选
    - `Workflows` Access: `Read and write` 获取用于更新 `.github/workflow` 下文件的权限

#### 你也可以创建更大权限的不限时token

- 建议使用上面的小权限token，这个token无法指定某一个仓库的权限，也就是token一旦泄露将有可能导致其他人直接自由访问和修改你的所有仓库代码
- 前往[https://github.com/settings/tokens/new](https://github.com/settings/tokens/new)创建
- 填写token名称，选择有效期
- `Select scopes` 勾选 `repo` 和 `workflow` 即可

#### 创建完毕后点击最底下的 `Generate token` 即可生成token，复制token并自己保存一下以备后续使用，关闭当前页面后将无法再看到它。

### 二、设置账号密码

#### 前往仓库设置创建变量

- Settings-->Secrets and variables-->Actions-->New repository secret
-
快捷跳转地址 [https://github.com/${你的github用户名}/mimotion/settings/secrets/actions](../../settings/secrets/actions)
- 点击右侧的 `New repository secret` 即可添加Secret

#### 添加名为 **PAT** 的Secret变量，值为第一步申请的token

- `PAT` 用于提交加密token数据，为了保证正常使用，一定要配置正确。

#### 添加名为 **AES_KEY** 的Secret变量，请自行创建一个长度为16个字符的字符串作为密钥

- 注意：密钥不要用中文，长度一定要是16个字符，否则可能出错。
- 如果你有多个账号，或者希望程序自动保存登录信息，就需要设置这个 `AES_KEY`。设置之后，程序会用这个密钥把各个账号的登录token信息加密保存起来。**请一定保管好你的密钥，不要泄露。**
- 同时，请确保你已经正确配置了 PAT 密钥，否则程序无法自动保存和提交信息到仓库。
- 更换 `AES_KEY` 后，旧的 `encrypted_tokens.data` 无法解密，程序会重新登录并使用新密钥保存Token。若未更换密钥却出现解密错误，请检查密钥和文件是否损坏。
- `encrypted_tokens.data` 由 `Update Steps` 自动维护。修改代码时保留该文件，不要用其他仓库的Token文件覆盖。

#### 添加名为 **CONFIG** 的Secret变量

- 需要注意Secret变量是密文，提交后无法查看，只能删除或用新值更新。建议在安全的密码管理器中保存配置数据，方便后期修改。
- CONFIG的内容：

  ```json
  {
    "USER": "abcxxx@xx.com",
    "PWD": "password",
    "MIN_STEP": "15000",
    "MAX_STEP": "18000",
    "PUSH_PLUS_TOKEN": "",
    "PUSH_PLUS_HOUR": "",
    "PUSH_PLUS_MAX": "30",
    "PUSH_WECHAT_WEBHOOK_KEY": "",
    "TELEGRAM_BOT_TOKEN": "",
    "TELEGRAM_CHAT_ID": "",
    "SLEEP_GAP": "5",
    "USE_CONCURRENT": "False"
  }
  ```

  | 字段名                     | 格式                                                                                                             |
  |-------------------------|----------------------------------------------------------------------------------------------------------------|
  | USER                    | 小米运动登录账号，仅支持小米运动账号对应的手机号或邮箱，不支持小米账号                                                                            |
  | PWD                     | 小米运动登录密码，仅支持小米运动账号对应的密码                                                                                        |
  | MIN_STEP                | 固定最低步数，每次执行均不会低于此值                                                                                         |
  | MAX_STEP                | 总步数上限；额外步数范围从0开始，按北京时间24小时周期增长，接近午夜时趋近MAX_STEP - MIN_STEP；必须不小于MIN_STEP                     |
  | PUSH_PLUS_TOKEN         | 推送加的个人token,申请地址[pushplus](https://www.pushplus.plus/push1.html)，工作流执行完成后推送每个账号的执行状态信息，如没有则不要填写                |
  | PUSH_PLUS_HOUR          | 限制只在某个整点进行pushplus的推送，值为整数，比如设置21，则只在北京时间21点XX分执行时才进行pushplus的消息推送。如不设置或值非数字则每次执行后都会进行推送                       |
  | PUSH_WECHAT_WEBHOOK_KEY | 企业微信推送通知的key，企业微信webhook机器人推送全地址为：https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={机器人的key}，这里配置{机器人的key} |
  | PUSH_PLUS_MAX           | 设置pushplus最大推送账号详情数，默认为30，超过30个账号将只推送概要信息：多少个成功多少个失败。因为数量太多会导致内容过长无法推送。具体最大值请自行调试                              |
  | TELEGRAM_BOT_TOKEN      | 设置telegram机器人的token，同时需要配置TELEGRAM_CHAT_ID，否则不会执行推送                                                            |
  | TELEGRAM_CHAT_ID        | 设置telegram的chatId，需要同时配置TELEGRAM_BOT_TOKEN，否则无法执行推送。关于这两个值如何获取，请前往官网查看。                                        |
  | SLEEP_GAP               | 多账号执行间隔，单位秒，如果账号比较多可以设置的短一点，默认为5秒                                                                              |
  | USE_CONCURRENT          | 是否使用多线程，实验性功能，未测试是否有效。账号多的可以试试，将它设置为True即可，启用后 `SLEEP_GAP` 将不再生效                                               |

### 三、多账户设置(如用不上请忽略)

- 多账户请用 **#** 分割 然后保存到变量 **USER** 和 **PWD**
- 理论上账户数量不受限制，但是实际要看github actions的资源和华米接口是否有限制，pushplus消息内容应该也有最大长度限制，反正具体上限请自行测试

#### 例如

```json
{
  "USER": "13800138000#13800138001",
  "PWD": "abc123qwe#abcqwe2",
  "MIN_STEP": "15000",
  "MAX_STEP": "18000",
  "PUSH_PLUS_TOKEN": "",
  "PUSH_PLUS_HOUR": ""
}
```

#### 注意 **#** 分隔的账号和密码数量必须匹配，否则将跳过执行

### 四、自定义启动时间

- 编辑 **.github/workflows/run.yml** 中的cron表达式即可修改固定计划。
- cron表达式格式为 `分 小时 日 月 星期`。GitHub Actions使用UTC，即**北京时间-8**。
- 当前北京时间07:00、15:00、23:00对应UTC23:00、07:00、15:00：

  ```yaml
  on:
    schedule:
      - cron: '0 7,15,23 * * *'
  ```

- 固定计划直接由 `run.yml` 控制，不使用 `CRON_HOURS` 变量或随机化工作流。
- GitHub Actions可能排队延迟，计划时间并不保证精确到分钟。手动执行属于额外运行，不计入每天3次的定时计划。

### 五、手动触发测试工作流

- 前往Actions,左侧选择 `Update Steps`
  ，快捷链接：[https://github.com/${你的github用户名}/mimotion/actions/workflows/run.yml](../../actions/workflows/run.yml)
- 本仓库已启用工作流。如果手动关闭过，请在Actions中选择 `Update Steps` 并点击 `Enable workflow`，否则不会定时执行。
- 点击右侧的`Run workflow`触发执行，触发后刷新即可查看执行记录。验证是否正确配置并执行刷步数。

### 六、感谢列表

本项目最初基于 [TonyJiangWJ/mimotion](https://github.com/TonyJiangWJ/mimotion) 的代码独立维护，保留原项目及贡献者的署名。

原项目基于 `https://github.com/xunichanghuan/mimotion(已被ban)`
和 [https://github.com/huangshihai/mimotion](https://github.com/huangshihai/mimotion) 项目修改，特此感谢

新版本登录需要加密，感谢[https://github.com/hanximeng/Zepp_API/blob/main/index.php](https://github.com/hanximeng/Zepp_API/blob/main/index.php)
里面提供的aes加密密钥。大家可以去给作者点个star

### 七、独立维护代码

- 本仓库不是GitHub fork，也不配置upstream远程或自动同步。代码修改直接提交到本仓库。
- 修改前先执行 `git pull --ff-only`，保留Actions自动维护的 `encrypted_tokens.data`、计划时间和执行记录。
- 修改工作流后，应验证固定计划，并确保只保留 `Update Steps`。

## 注意事项

1. 每天在北京时间07:00、15:00、23:00定时运行3次。执行后不会改写cron或随机分钟，也不会因为随机化而在同一小时重复执行。

2. 多账户的数量和密码请一定要对上 不然无法使用!!!

3. 启动时间得是UTC时间!

4. 如果支付宝没有更新步数，到小米运动->设置->账号->注销账号->清空数据，然后重新登录，重新绑定第三方。建议去开头提到的网站测试账号是否正常

5. 小米运动不会更新步数，只有关联的会同步！！！！！

6. 本仓库独立维护，部署及问题排查以本仓库的代码和文档为准。

7. 请注意，账号不是 [小米账号]，而是 [小米运动/ZeppLife] 的账号。

8. 最低步数固定为MIN_STEP，只对MAX_STEP - MIN_STEP的差值按北京时间24小时周期计算随机额外步数。
   配置15000–18000时，10:00的随机总步数为15000–16250；每天00:00重新从15000开始。可通过CONFIG中的MIN_STEP和MAX_STEP修改范围。

9. cron的执行根据github actions的资源进行排队，并不是百分百按指定的时间进行运行，请知悉。

10. 新版本接口有限制，同ip登录过多账号可能会429，请自行测试。

### 查看执行记录

- 前往 [Actions](../../actions) 可以查看所有工作流的执行历史
    - `Update Steps #41: Scheduled` 代表是定时任务触发，`Update Steps #33: Manually run by xxx` 代表手动触发
- 点击其中一条记录，可以查看执行详情，这里以 `Update Steps` 为例：
    - 详情界面 `Jobs` 可以查看到一个 `build` ，点击它查看执行步骤
    - 执行步骤中主要关注 `Update Steps` ，点击 `Update Steps` 展开详情
    - 展开后便可以查看到执行日志，如果执行成功，则会显示每个账号当前随机的步数是多少
    - 如果执行失败，则需要根据实际情况分析具体失败原因
- `cron_change_time` 仅保留旧的随机计划历史，当前计划以 `.github/workflows/run.yml` 为准。

## 本地开发

复制 `.env.example` 文件为 `.env`，并在 `.env` 中填入你的配置信息
```shell
cp .env.example .env
```
**注意**：`.env` 文件已添加到 .gitignore 中，请不要推送到代码仓库中以免造成数据泄露

创建 python 虚拟环境
```shell
python3 -m venv venv
```

激活虚拟环境
```shell
# Windows
./venv/Script/Activate

# Linux
source ./venv/bin/activate
```

安装依赖
```shell
pip install -r requirements.txt
```

执行脚本修改步数
```shell
python3 main.py
```