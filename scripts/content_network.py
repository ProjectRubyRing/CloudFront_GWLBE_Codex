from report_model import section, row as R

section(9, "業務通信の行き", "検査を通って本を取りに行く順路です。VPC Link側のENIがAZ-A、ALBもAZ-Aの基本例を示し、クロスAZは15章で展開します。", [
R("F01 公開APIまで", "ロボットが通行証付き注文を受付へ渡します。", "インターネット上のクライアントからRegional APIの公開入口へHTTPSで送ります。WAF→Cognito scope認可を通過します。", "これは利用者VPC内のIGW経由ではありません。拒否された要求はここで止まります。", "S11 S12 S13 S14"),
R("F02 VPC Linkから送信", "受付が敷地内の出口から注文を出します。", "API GatewayはVPC Link V2を使い、選択サブネットのENIからinternal ALBへ統合接続を作ります。例：10.20.10.10:53000→10.20.30.10:443。", "IP/portは説明用。実際のENI/ALBアドレスは変動し得ます。sourceは外部クライアントIPそのものではありません。", "S03 S04"),
R("F03 ルートを選択", "『ALB区画へ行くなら検査口へ』という道しるべを見ます。", "Link-Aのルート表でALB-A subnet 10.20.30.0/24→GWLBE-Aを選びます。VPC全体の10.20.0.0/16→localより具体的な宛先が優先です。", "0.0.0.0/0だけをGWLBEへ向けても、より具体的なlocalが勝ち、この通信は検査を迂回します。", "S15"),
R("F04 GWLBEに入る", "検査本部へ送る出入口を通ります。", "業務VPC内のGWLBE-Aが、アカウントSのGWLB endpoint serviceへ通信を運びます。業務パケットの最終宛先は引き続きALBです。", "アプリのHTTPS宛先をGWLBEのIPやURLへ置き換える方式ではありません。", "S16 S34"),
R("F05 GWLBがFWを選ぶ", "係が今回の検査担当を決めます。", "GWLBはフローの情報に基づいてVM-Seriesターゲットを選びます。通常は5-tupleのフロー固定が働き、同一通信を担当FWに継続して送ります。", "HTTPリクエストごとに必ず別FWへ分散するわけではありません。接続再利用の影響があります。", "S17 S19"),
R("F06 GENEVEで運ぶ", "元の注文を検査用の袋に入れます。", "GWLB↔FWでは元のIPパケットをGENEVE/UDP 6081で包みます。外側はGWLB/FW間、内側はLink ENI/ALB間のアドレスです。", "ALBの443とFWの6081は別の層のポートです。SG/NACLで取り違えないようにします。", "S17 S63"),
R("F07 FWが検査", "検査員が危険な荷物か確かめます。", "VM-Seriesが内側の通信を取り出し、設定されたsecurity policyや脅威防御を適用します。TLS本文を調べる場合は16章の復号が別途必要です。", "拒否時はdrop/reset等の設定に従います。HTTPの分かりやすい403が必ず返るとは限りません。", "S21 S22"),
R("F08 同じ出入口へ戻る", "検査後、元の学校の出入口へ返します。", "FW→GWLB→GWLBE-Aと戻ります。主例は元パケットのアドレスを維持する透過検査で、FWのSNATで業務経路を作り替えません。", "FWからTGWやIGWへ抜けてALBを直接目指す方式とは混在させません。", "S17 S21"),
R("F09 ALBへ配送", "検査済みの注文を案内係へ届けます。", "GWLBE-A subnetのルート表は業務VPC宛てをlocalとし、元の宛先ALBへ送ります。ALB側SGもLink subnetからの443を許可します。", "GWLBE subnetからALB宛てを再び同じGWLBEへ向けると循環します。", "S15 S16"),
R("F10 ALBで受信", "案内係が注文用紙を開いて担当を選びます。", "HTTPS listenerのALBがTLSを終端し、Host/pathのlistener ruleでtarget groupを選びます。必要なら独立したJWT検証も追加できます。", "GWLBではなくALBがHTTPを見て業務サービスへ振り分けます。", "S25 S29 S64"),
R("F11 taskへ接続", "案内係が図書室の担当者に注文を伝えます。", "ALBはECS taskのIP:portへ新しい接続を作ります。例：ALBのbackend側→10.20.40.50:8443。awsvpc taskはip targetとして登録します。", "このALB↔task区間は、主例ではlocal経路であり今回のGWLBE検査区間外です。", "S24 S25"),
R("F12 アプリが処理", "担当者が本を探し、結果を作ります。", "task内のアプリが入力検証、データごとの認可、業務処理を実施し、HTTP status/bodyを生成します。", "ネットワーク検査合格は業務データへの全権限を意味しません。アプリの認可と安全な実装も必要です。", "S07 S24"),
])

section(10, "応答の戻り", "『来た線を逆にたどる』だけでなく、接続ごとに分けて考えます。ECSの応答はいったんALBへ戻り、ALBがVPC Link側の接続へ返します。", [
R("R01 task→ALB", "図書室の担当者が案内係へ本を渡します。", "taskはALBが開始したbackend接続上でHTTP応答を返します。taskが外部クライアントへ直接送信するのではありません。", "task subnetの0.0.0.0/0がNAT向きでも、ALBのプライベートIP宛て応答はより具体的なlocal経路です。", "S15 S25 S64"),
R("R02 ALBが応答を中継", "案内係が受付へ返す荷物に載せ替えます。", "ALBはfrontend接続であるLink ENI↔ALBへ応答を出します。例：10.20.30.10:443→10.20.10.10:53000。", "ALB↔taskの5-tupleと、ALB↔Link ENIの5-tupleは別です。", "S25 S64"),
R("R03 戻りルートを選択", "『受付の出口へ戻すなら同じ検査口へ』を選びます。", "ALB subnetのルート表で10.20.10.0/24→GWLBE-Aを選びます。Link-B宛てならGWLBE-Bを選ぶ別ルートを設けます。", "ALB自身のAZだけでGWLBEを選ぶと、クロスAZの応答が往路と異なるendpointへ流れます。", "S15 S16 S19"),
R("R04 GWLBE→GWLB", "学校から検査本部へ、戻す荷物を渡します。", "戻りパケットも同じGWLBE-Aを経由します。GWLBは反対方向の通信を同じフローとして扱い、担当VM-Seriesへ送ります。", "ルートで同じendpointを通すことと、GWLBのflow stickinessが両方必要です。", "S17 S19 S21"),
R("R05 FWが応答を検査", "行きの注文を覚えた係員が、返す本を確認します。", "FWは既存セッションの戻りとして確認し、設定に応じて脅威や内容も検査します。TLSが未復号なら暗号化本文の内容までは見えません。", "allowログだけで復号成功と判断せず、decryptionやthreatの証跡と照合します。", "S21 S22"),
R("R06 FW→GWLB→GWLBE", "検査を終え、同じ学校へ返します。", "許可された応答はGENEVEでGWLBへ戻り、GWLBE-Aから業務VPCへ再投入されます。", "検査アカウントからインターネットへ直接クライアントに返す構成ではありません。", "S17 S21"),
R("R07 Link ENIへ配送", "受付につながる出口へ返します。", "GWLBE subnetのlocal routeで10.20.10.10へ届きます。API GatewayはVPC Linkの統合応答として受け取ります。", "戻りにもNACLの許可が必要です。SGのstatefulな応答許可とNACLのstatelessな規則を区別します。", "S03 S15 S16"),
R("R08 公開接続へ応答", "受付がロボットへ答えを返します。", "API GatewayがクライアントとのHTTPS接続上で結果を返します。主構成ではCognito用CloudFrontやCognitoを経由しません。", "この戻りに新しいaccess tokenが発行されるわけでもありません。", "S06 S13"),
R("R09 途中の拒否", "入口で止めたら、奥の係員は何も受け取りません。", "WAF/authorizerで止まった場合はその地点からエラーが返り、後段通信は作られません。FWがdropした場合はAPI側のtimeout等として見える可能性があります。", "ALB/taskログがないことが、その層の障害を意味するとは限りません。最終到達地点を探します。", "S12 S35 S37"),
R("R10 返す順序と再試行", "返事が遅くても、本の注文が失敗したとは限りません。", "アプリが処理を完了した直後に応答経路が失敗すると、呼出側は失敗、アプリは成功という状態になります。", "更新APIには業務上の冪等キー等を用意し、timeout時の無条件な二重実行を防ぎます。", "設計上の考慮"),
])

section(11, "VPCLinkV2詳細", "VPC LinkはAPI Gatewayの外向き統合接続です。APIの入口をprivateにするInterface endpoint、検査用GWLBEとは役割が異なります。", [
R("V1とV2", "古い通路と新しい通路で、つなげる受付が違います。", "V1はRESTの従来方式でNLB対象。V2はALB/NLBを対象にでき、現在はRESTでも使用できます。", "HTTP APIで以前からALBを使えた事実と、RESTへの2025年拡張を分けて理解します。", "S01 S02 S52 S55"),
R("ENIの作成", "敷地の指定区画に出口を作ります。", "V2作成時にsubnetとSGを指定すると、API Gatewayが利用者アカウントにENIを作成・管理します。状態がAVAILABLEになって利用します。", "IP残数不足や対応AZを確認します。ENIを手動変更・固定する前提では設計しません。", "S03"),
R("配置を変える場合", "通路の出口の場所を変えるなら、新しい通路を用意します。", "作成後のV2はsubnetや関連付けるSGの一覧を変更できません。変更が必要なら新VPC Linkを作って統合を切り替えます。", "SGそのもののルール更新と、VPC Linkに関連付けるSG ID一覧の変更は別です。", "S03"),
R("対象ARNの違い", "『どの案内係へ送るか』と『どの名前で話すか』は別欄です。", "現行RESTのprivate integrationではintegration-targetにALB自体のARNを指定します。URIはHTTPS/port/pathとHost・証明書名の検証に関わります。", "HTTP APIで使うlistener ARNの例をRESTへそのまま移植しません。", "S04"),
R("HTTPSを明示", "敷地内でも鍵付きの会話を選びます。", "REST private integrationの既定はHTTPです。本設計の例はhttps://backend.example.com:443/...を使用し、ALBの証明書名と整合させます。", "HTTPSという名前だけで設定済みと考えず、URI、listener、TLS名検証の結果を確認します。", "S02 S04"),
R("ステージ名の付加", "受付が付けた区分名が、注文先へも付くことがあります。", "private integrationではAPIのstage部分が後段パスに含まれます。/prod/books/42を想定せず/books/42だけ待つアプリとは不一致になり得ます。", "ALB/app側で受けるか、RESTのrequest override等で変換するか決め、実際のHost/pathをログで検証します。", "S02 S04"),
R("同一アカウント条件", "通路と案内係は業務側がそろえて管理します。", "直接の統合先LB、VPC Link、REST APIは同一AWSアカウントで所有します。検査サービスを別アカウントへ分離することはGWLBE側で実現します。", "同一アカウント制約がないかのように、別アカウントALBのARNをそのまま指定しません。", "S02 S32"),
R("60日の非稼働", "長く使わなかった通路は再準備に時間がかかります。", "60日間trafficがないVPC LinkはINACTIVEとなりENIが削除されます。再アクセス時に再作成されるまで数分、依存するAPI要求が失敗することがあります。", "DR環境・低頻度バッチでは状態監視と復帰時間を試験します。", "S03"),
R("Private APIとの違い", "外から受付へ入る通路と、受付から図書室へ入る通路は別です。", "Private APIはクライアント→API Gatewayの入口をInterface endpointで非公開化します。private integrationはAPI Gateway→backendを非公開化します。", "公開Regional API＋private integrationは矛盾しません。今回はこちらです。", "S02 S13 S58"),
R("適用範囲の確認", "新しい通路にも使える場所と相手の決まりがあります。", "VPC Link V2の対応Region/AZを公式一覧で確認します。RESTのprivate integrationでCloud Mapを直接使えるとは扱いません。", "CLIにapigatewayv2と出てきてもREST APIをHTTP APIへ変更したわけではありません。", "S02 S03"),
])

section(12, "GWLBとPaloAlto", "検査の往復は『GWLBE→GWLB→FW→GWLB→同じGWLBE』です。FWは道の途中に透明に挿入され、元のパケットを検査して戻します。", [
R("L3で透明に挿入", "荷物の宛先を書き換えず、検査所に寄り道させます。", "GWLBはIPパケットを扱うL3のサービスです。ALBのようにHTTP URLから業務ターゲットを選ぶのではなく、セキュリティアプライアンスへ分配します。", "名前にLoad BalancerがあってもALB/NLBとは役割が異なります。", "S17"),
R("内側と外側", "学校宛ての封筒を、本部宛ての大きな袋に入れます。", "内側例は10.20.10.10→10.20.30.10、TCP 443。外側はGWLBノード↔FWデータIFで、GENEVE/UDP 6081です。", "FWログのoriginal sourceと、AWS SGが扱う外側通信を分けて追います。", "S17 S63"),
R("送り状の役割", "どの学校の入口へ返すかを送り状で覚えます。", "GENEVEにはGWLB連携のメタデータがあり、アプライアンスは対応した処理で戻します。単にUDP6081を開けた一般サーバーでは検査FWになりません。", "VM-SeriesのGWLB連携、plugin/PAN-OSの対応、health checkを製品手順でそろえます。", "S21 S63"),
R("5-tuple", "差出人・差出窓口・宛先・宛先窓口・運び方で荷物を区別します。", "source IP、source port、destination IP、destination port、protocolが5要素です。GWLBは通常この単位で担当FWを固定します。", "同じtokenでも別TCP接続なら別フローです。1本のkeep-alive接続に複数のHTTP要求が乗る場合もあります。", "S19"),
R("セッション状態", "検査員は『この返事はさっきの注文の返事』と覚えています。", "VM-SeriesはTCPの開始・継続等を踏まえてセッションを管理します。経路が別FWへ変わると、そこに必要な状態がない場合があります。", "GWLBを使うだけでFW間のセッション同期や無停止引継ぎが自動保証されるわけではありません。", "S19 S20 S21"),
R("SNATしない前提", "検査員の名前に差出人を書き換えない運用です。", "本例の透過経路は内側のLink/ALBアドレスを維持します。NAT、overlay routing、別出口を使うFW構成は別の設計です。", "既存VM-SeriesにNAT等がある場合は、そのまま本例のルートだけ追加して成立すると判断しません。", "S15 S21"),
R("クロスアカウント", "検査員が別の組織にいても、専用口で荷物を往復できます。", "GWLBEはPrivateLinkのendpoint serviceへ接続します。業務VPC全体を検査VPCにピアリングして広く到達可能にすることを必須にしません。", "ただし複合構成のネットワークとFWのサポート条件は実際の製品バージョンで確認します。", "S16 S34"),
R("AZとcross-zone", "普段は同じ校舎側の検査員へ渡します。", "GWLBのcross-zoneは既定で無効です。本例もAZごとにFWを配置する考え方です。有効化すると他AZのFWが選ばれ得ます。", "cross-zone設定は処理分散の話、同じGWLBEへ戻すルートは対称性の話です。片方で他方を代替しません。", "S18 S19"),
R("全FW異常時", "全員が体調不良でも、勝手に検査所の横道を開くわけではありません。", "GWLBは全targetがunhealthyのとき、unhealthy targetへ新規フローを送る場合があります。FWを飛ばしてALBへ直接通す意味ではありません。", "『fail openだから検査なしで成功する』と解釈しません。実際のFWが転送できなければ通信は失敗します。", "S20"),
R("failoverの限界", "別の検査員に変わると、途中の注文はやり直しになることがあります。", "既存フローの既定はno_rebalanceです。rebalanceへ変更すると異常targetから振り直せますが、新FWの状態不足で接続が切れる可能性は残ります。", "新規通信の回復と、既存通信の無停止継続を別々に試験します。", "S19 S20"),
R("MTUと包装分", "袋を追加した分、大きな荷物が通路に入らないことがあります。", "現行GWLB文書ではinterface MTUは8,500 bytes、GENEVE追加分は68 bytesです。最大サイズを扱うFWは少なくとも8,568 bytesを受けられる必要があります。", "GWLBのIP fragmentation/PMTUD制約を確認し、大きい通信を試験します。HTTP本文サイズとIPパケットサイズは同じではありません。", "S18"),
R("検査範囲の証明", "検査所の通行記録と検査内容の記録を照合します。", "正常応答だけではFW通過を証明できません。FW session/traffic logとVPC側の通信情報を突き合わせ、許可・拒否・復号の各テストを分けます。", "暗号化状態やpolicy次第でApp-ID/脅威検知の範囲が変わります。『全攻撃を検知』という説明にはしません。", "S21 S22 S35"),
])

SUBNETS = [
    ("Link-A", "10.20.10.0/24", "A", "VPC Link ENI", "RT-Link-A"),
    ("Link-B", "10.20.11.0/24", "B", "VPC Link ENI", "RT-Link-B"),
    ("Endpoint-A", "10.20.20.0/24", "A", "GWLBE-A", "RT-Endpoint-A"),
    ("Endpoint-B", "10.20.21.0/24", "B", "GWLBE-B", "RT-Endpoint-B"),
    ("ALB-A", "10.20.30.0/24", "A", "internal ALB", "RT-ALB-A"),
    ("ALB-B", "10.20.31.0/24", "B", "internal ALB", "RT-ALB-B"),
    ("Task-A", "10.20.40.0/24", "A", "ECS task", "RT-Task-A"),
    ("Task-B", "10.20.41.0/24", "B", "ECS task", "RT-Task-B"),
]

section(13, "サブネット設計", "すべて説明用IPv4 CIDRです。業務VPCは10.20.0.0/16、検査VPCは10.80.0.0/16。実際には既存CIDR・接続先との重複を確認して置き換えます。", [
    R(name, f"AZ-{az}にある{role}専用の区画。", f"CIDR：{cidr}\n関連付け：{rt}\n業務アカウントA／業務VPC内。", "同一subnet内の迂回を避けるため、Link・Endpoint・ALB・Taskを役割ごとに分離します。", "設計例・S15 S16")
    for name, cidr, az, role, rt in SUBNETS
] + [
R("検査VPCの区画", "本部の配分係と検査員の場所。", "GWLB：10.80.10.0/24(A)、10.80.11.0/24(B)。FWデータ：10.80.20.0/24(A)、10.80.21.0/24(B)。管理用の区画はさらに分けます。", "FW→GWLBのGENEVE復路を成立させます。業務10.20.0.0/16への直接TGWルートは本例には不要です。", "設計例・S17 S33"),
R("専用subnetの理由", "同じ部屋の中の受け渡しには、廊下の道しるべが効きません。", "同一subnetの相手へ直接届く経路を、subnet間のmore specific routeで途中検査へ寄り道させることはできません。", "ALBとLinkを分け、endpoint用RTを別にすることが、この挿入方式の成立条件です。", "S15"),
])

ROUTES = []
for table in ["RT-Link-A", "RT-Link-B", "RT-ALB-A", "RT-ALB-B", "RT-Endpoint-A", "RT-Endpoint-B", "RT-Task-A", "RT-Task-B"]:
    ROUTES.append((table, "10.20.0.0/16", "local", "VPC内の基本経路。下記の/24があればそちらが優先。"))
for az in ["A", "B"]:
    for dest in ["10.20.30.0/24", "10.20.31.0/24"]:
        ROUTES.append((f"RT-Link-{az}", dest, f"GWLBE-{az}", f"Link-{az}始点のALB向け要求は、ALBのAZに関係なく同じendpointへ。"))
    ROUTES.append((f"RT-ALB-{az}", "10.20.10.0/24", "GWLBE-A", "Link-A宛ての応答を、往路と同じendpointへ。"))
    ROUTES.append((f"RT-ALB-{az}", "10.20.11.0/24", "GWLBE-B", "Link-B宛ての応答を、往路と同じendpointへ。"))

section(14, "ルート表", "この表は挿入対象の業務通信に必要な経路だけを示します。GWLBE-A/Bは実際には各vpce-IDへ置き換えます。実環境の既存ルートを削除する手順ではありません。", [
    R(table, f"宛先 {destination}", f"次の送り先：{target}\n{purpose}", "targetがGWLBEの場合は同じ業務VPC内のendpoint IDを指定します。localからのより具体的な転送先は相手subnet全体です。" if target != "local" else "EndpointのRTにALB/Link宛てのGWLBE再送ルートを追加しないでください。管理用・外向き通信は別途設計。", "設計例・S15 S16")
    for table, destination, target, purpose in ROUTES
] + [
R("/24が/16より優先", "宛名が詳しい道しるべを使います。", "10.20.30.10は10.20.0.0/16にも10.20.30.0/24にも該当します。より長いprefixである/24を選ぶため、local直行からGWLBEへの寄り道へ変わります。", "ALBの1個の動的IPに/32を設定する案ではなく、subnet全体の/24を使用します。", "S15"),
R("管理通信を混ぜない", "本の配送路と、職員の出勤路は別です。", "本表に0.0.0.0/0がないのは対象通信に不要だからです。ECS起動・更新・監視の通信やFW管理通信には追加の経路が必要になり得ます。", "既存route tableへ適用する際は差分と影響を評価します。この表はそのまま全置換するテンプレートではありません。", "設計上の考慮"),
])

section(15, "ルート動作例", "4通りのAZ組合せを確認します。endpointの選択を『VPC Linkの送信元subnet』にそろえると、ALBノードが別AZでも往復を同じ検査口にできます。", [
R("Case 1：A→A", "同じ校舎側で往復します。", "行き：Link-A→E-A→検査→E-A→ALB-A。\n戻り：ALB-A→E-A→検査→E-A→Link-A。", "Link-AのALB-A宛て/24、ALB-AのLink-A宛て/24はともにE-Aです。E-AはGWLBE-Aの略です。", "設計例・S15 S19"),
R("Case 2：A→B", "別校舎へ届けても、同じ検査口へ戻します。", "行き：Link-A→E-A→検査→E-A→ALB-B。\n戻り：ALB-B→E-A→検査→E-A→Link-A。", "ALB-Bが近くのE-Bを選ぶのではなく、宛先Link-AのsubnetによりE-Aを選びます。AZをまたぐ費用・遅延を考慮します。", "設計例・S15 S16 S19"),
R("Case 3：B→A", "反対側から始まった注文は、反対側の検査口にそろえます。", "行き：Link-B→E-B→検査→E-B→ALB-A。\n戻り：ALB-A→E-B→検査→E-B→Link-B。", "ALB-A/Bの両方にLink-B宛て→E-Bのルートが必要です。", "設計例・S15 S19"),
R("Case 4：B→B", "B側の校舎だけでも同じルールです。", "行き：Link-B→E-B→検査→E-B→ALB-B。\n戻り：ALB-B→E-B→検査→E-B→Link-B。", "構成要素を2AZに置くだけでなく、両側のルートを同じ規則でそろえます。", "設計例・S15 S19"),
R("誤り1：行きだけ検査", "出発時は検査して、帰りは裏道を使ってしまいます。", "Link→ALBの/24だけ追加し、ALB→Linkの/24を忘れると、戻りはlocalへ流れます。成功する場合でも要求した往復検査にはなりません。", "片方向しかログがない場合は、FW設定だけでなく両subnetのRTを確認します。", "S15 S18 S21"),
R("誤り2：各AZの最寄り", "行きと帰りで別の検査員になってしまいます。", "A→ALB-Bの要求がE-A、ALB-B→Aの応答がE-Bとなる例です。FW状態やendpointの選択が一致しないリスクがあります。", "『戻りは必ずALBと同じAZのGWLBE』という単純ルールは採用しません。", "設計上の推論・S16 S19"),
R("誤り3：循環", "検査を終えても、また検査口へ戻されます。", "Endpoint-AのRTにもALB宛て→E-Aを追加すると、戻ってきた検査済みパケットの配送を妨げます。", "送り出すLink/ALBのRTと、検査後に届けるEndpointのRTを分けます。", "設計上の推論・S15"),
R("障害時の読み方", "道が壊れたら、前の荷物が必ず無傷で届くわけではありません。", "E-A/AZ-Aの障害時、A始点の既存フローは影響を受けます。新規要求が健全なB側で作られればBの経路を使えますが、切替タイミングや再接続は要試験です。", "本表は対称性を説明する静的設計です。AZ障害の自動復旧時間を保証する表ではありません。", "S03 S19 S20"),
])
