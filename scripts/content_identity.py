from report_model import section, row as R

section(1, "最初に押さえること", "最初の結論：トークンをもらう通信と、そのトークンで業務APIを呼ぶ通信は別です。公開サービスの入口と、お客様のVPC内の通信を分けると全体が理解できます。", [
R("構成は条件付きで成立", "ロボットが通行証をもらい、受付と検査所を通って図書室へ行くイメージです。", "Regional REST API→VPC Link V2→internal ALBが現在の基本線です。そのVPC内区間に、別アカウントのGWLB/VM-SeriesをGWLBEとサブネットルートで挿入する設計例を示します。", "個々の機能は公式確認済み。組み合わせ全体は設計例であり、実環境での疎通・復号・障害試験は未実施です。", "S01 S02 S15 S21"),
R("認証と業務は2往復", "通行証を受け取ってから、別の窓口へ本を頼みます。", "①クライアント→CloudFront→Cognito→クライアント。②クライアント→Regional API→検査→ALB→ECS→クライアント。トークンがCognitoから自動的にECSへ転送されるわけではありません。", "トークンは呼出側が受け取り、業務リクエストのAuthorizationヘッダーへ設定します。", "S05 S06 S07"),
R("IGWの位置を修正", "学校の門は学校の敷地用です。町のすべての受付に共通の門ではありません。", "Internet Gatewayは特定VPCにアタッチする部品です。インターネットから公開Regional API Gatewayへ到達するとき、お客様のVPCのIGWを必ず通るという構成にはなりません。", "主構成のAPI Gateway→VPC Link→ALBにIGWは不要。呼出元がVPC内なら、その外向き通信にIGW/NATが関わる場合があります。", "S13 S14"),
R("RESTとV2は両立", "新しい連絡通路を、いつもの受付でも使えるようになりました。", "2025-11-21にREST APIのALB直接プライベート統合が発表されました。VPC Link V2という名前からHTTP API専用と判断しないでください。", "古いREST→VPC Link V1→NLB→ALBの説明を、現在の新規構成にそのまま当てはめません。", "S01 S52"),
R("GWLBとGWLBEの配置", "各学校に検査所へつながる出入口を置き、検査員を本部に集めます。", "業務アカウントAのVPCにGWLBE、インターネット接続/検査アカウントSのVPCにGWLBとPalo Alto Networks VM-Seriesを置きます。両者はendpoint serviceで結びます。", "アカウント名が『インターネット接続』でも、今回の検査の往復はPrivateLink経由です。TGWやIGWを自動的に通る意味ではありません。", "S16 S17 S34"),
R("帰り道も設計する", "検査した係員に、帰りの荷物も見てもらいます。", "状態を持つFWは通信開始からの流れを覚えます。行きだけGWLBE、戻りはlocal直通という設計では検査が欠けます。両方向を同じGWLBEと同じFWフローへ通します。", "ALBが別AZのノードでも成立するルート表を14・15章に記載しています。", "S15 S19 S21"),
R("HTTPSの見える範囲", "鍵付きの箱は、外の宛先は見えても中の文章は読めません。", "GWLB/GENEVEが自動でTLSを復号することはありません。Palo Altoで本文を検査するには、適切なSSL Inbound Inspection、証明書・秘密鍵、対応バージョン等が必要です。", "『FWを通過した』と『HTTP本文を検査した』を別の検証項目にします。", "S17 S21 S22"),
R("検査対象の区間", "受付から案内係までの通路を検査します。図書室内の通路は別です。", "挿入場所はVPC Link ENI↔ALBの区間です。ALB↔ECSはALBが作る別接続です。今回のルートだけでALB↔ECSやECSの外向き通信まで検査されるわけではありません。", "APIキャッシュで後段へ行かない要求や、WAF/認可で拒否された要求もFWへ到達しません。", "S03 S15 S64"),
R("読むときの前提", "地図の住所は、しくみを学ぶための例です。", "例は東京リージョン、IPv4、2AZ、単一業務VPC、internal ALB、ECS awsvpcです。CIDR、ドメイン、ポート、時刻は説明用で、実在するお客様の設定を示しません。", "AS-IS設定を調べた監査報告ではありません。事実・設計上の選択・要実機確認を区別しています。", "設計前提"),
R("小学生向けの読み方", "まずお話と地図を読み、そのあと通行証と道順を見ます。", "04章のたとえ→02章の全体図→06章の認証→09・10章の行き帰り→14・15章のルート→16章の暗号化、の順に読みます。技術者は11〜23章を設計確認に使えます。", "各行は『やさしい説明』『仕組み』『設定と注意』『出典』の順です。たとえは理解用で、厳密な仕様は詳細欄を優先します。", "編集方針"),
])

section(4, "たとえと登場人物", "ずかんを取り寄せるロボットの話で考えます。認証は『だれか』、認可は『何をしてよいか』、検査は『危険なものがないか』です。", [
R("呼出クライアント", "図書室へ本を頼むロボット。", "定期バッチ、サーバー、他社システム等です。人のブラウザでログインする代わりに、自分のclient ID/secretで機械として認証します。", "secretを安全に保持できるサーバー側のconfidential clientを使います。", "S07 S08"),
R("CloudFront", "世界各地にある案内窓口。", "利用者に近いエッジで接続を受けます。この資料ではCognitoカスタムドメインにCognitoが用意するCloudFrontを採用します。", "近い窓口でも、トークンを発行するCognitoの処理そのものが世界中で行われる意味ではありません。", "S05 S43"),
R("Cognito User Pool", "通行証を発行する事務室。", "アプリクライアントと許可scopeを管理し、署名付きaccess tokenを発行します。M2Mでは人のユーザーがログインする必要はありません。", "User Poolという名称でも、M2Mの主体はアプリです。IAM権限を渡すIdentity Poolとも別です。", "S07 S09 S65"),
R("client ID / secret", "ロボットの登録番号と、本人だけが知る合言葉。", "client IDは識別子、secretは認証に使う秘密です。業務APIにsecretを配らず、Cognitoが発行した短命のトークンを提示します。", "IDとsecretを同じ意味にしません。secretやtokenをログ・URL・Excelへ実値で記録しません。", "S08 S41"),
R("access token / scope", "期限と使える部屋が書かれた通行証。", "JWTに期限やbooks-api/books.readのようなscopeが入ります。scopeは許可された操作の名前です。", "通行証を持っているだけで全操作が許されるわけではありません。", "S07 S09"),
R("API Gateway / REST API", "本の注文を受ける受付と、受付で受け付ける注文メニュー。", "API GatewayがREST APIを提供します。Regional API GatewayとRegional REST APIを別々のネットワーク装置2台と考える必要はありません。", "GET /books/42等のメソッド・パスごとに認可と統合を設定します。", "S11 S13"),
R("AWS WAF", "受付で注文用紙を調べる係。", "HTTPリクエストのURI、ヘッダー、本文等をルールに照らして調べます。SQLインジェクション等への対策を構成できます。", "APIステージに関連付ける処理です。独立した通過先IPとしてルート表へ書く装置ではありません。", "S12 S27"),
R("Cognito authorizer", "通行証の印と有効期限、使える部屋を確認する係。", "信頼したUser Poolのtokenを使ってRESTメソッドへのアクセスを判断します。M2Mではメソッドに必要なOAuth scopeを設定します。", "HTTP APIのJWT authorizerの設定手順と混ぜません。", "S11 S28"),
R("VPC / subnet / AZ", "学校の敷地、敷地の区画、離れた校舎。", "VPCは隔離されたネットワーク、subnetはそのIP範囲の区切り、AZはリージョン内の障害分離単位です。1つのsubnetは1つのAZに属します。", "物理的に隣かどうかを表す比喩ではなく、接続と障害の境界として読みます。", "S03 S16 S44"),
R("Internet Gateway", "学校の敷地と公道をつなぐ門。", "VPCとインターネットをつなぐ部品です。アカウントに属するすべてのマネージドサービスを囲う門ではありません。", "公開API Gatewayの手前へ利用者のIGWを描かないことが重要です。", "S14"),
R("VPC Link V2 / ENI", "外の受付から敷地内へ入る連絡通路と出口。", "API Gatewayが選択サブネットへENIを作り、そこからVPC内のLBへ通信します。ENIは仮想ネットワークカードです。", "ENIの所在サブネットのルートとSGが設計上の要点です。", "S03"),
R("GWLBE", "検査本部へ荷物を送って、検査後に受け取る出入口。", "Gateway Load Balancer endpointの略です。ルート表の次の送り先に指定します。HTTPの宛先URLではありません。", "GWLBE自体が脅威判定をするわけではありません。", "S16 S34"),
R("GWLB / Palo Alto", "検査員へ仕事を振り分ける係と、実際の検査員。", "GWLBはフローをVM-Seriesへ分配します。VM-Seriesがポリシー、App-ID、脅威防御等の設定に従って許可・遮断します。", "GWLBとFWを同一機能として扱いません。必要な機能・ライセンス・性能はVM-Series構成に依存します。", "S17 S21"),
R("GENEVE", "元の荷物を、検査用の送り状付き袋に入れる方法。", "元のIPパケットを包み、GWLBとFWの間で運びます。FWが内側を検査し、所定の形式でGWLBへ返します。", "包装は暗号化そのものではありません。元のTLS暗号は別に残ります。", "S17 S63"),
R("ALB / ECS task", "注文を担当の机へ振り分ける案内係と、実際に本を探す担当者。", "ALBはHTTPのHost/path等でターゲットへ振り分け、ECS task内のアプリが業務処理をします。ECS serviceはtaskの数と配置を管理します。", "通信が届くのはtaskのIP/portです。ECS管理APIを毎回経由するわけではありません。", "S24 S25"),
R("ルート / SG / NACL", "道しるべ、部屋の入場規則、区画の出入り規則。", "ルートはどこへ送るか、SGはENI等で通信を許すか、NACLはsubnet境界の通信を許すかを決めます。", "道があっても許可がなければ届かず、許可があっても道が違えば検査を通りません。", "S15 S16"),
])

section(5, "構成と配置", "管理上のアカウント境界と、パケットが通るVPC境界を別々に示します。主構成では業務VPCに4種類のサブネットをAZごとに用意します。", [
R("アカウントA：業務", "図書室を運営する組織。", "Regional REST API、regional WAF web ACL、VPC Link V2、業務VPC、internal ALB、ECSを所有します。例ではCognito User PoolもAに置きます。", "API・VPC Link・統合先LBの同一アカウント制約と、Cognito poolの配置条件を混同しません。", "S02 S65"),
R("アカウントS：検査", "複数の学校を担当する検査本部。", "Security VPCにGWLB、GENEVE target group、VM-Series群、endpoint serviceを置きます。管理用通信やPanorama等は業務データ経路と分けます。", "アカウントSのIGW/NATが存在しても、今回の検査データをそこへ送る必要はありません。", "S17 S21 S32"),
R("CloudFrontの所有", "Cognitoが用意した案内窓口を使います。", "Cognitoカスタムドメインを設定するとAWS管理のCloudFront distributionが作られます。Cognitoの論理リソースがアカウントAにあっても、distribution設定を利用者が自由変更できるものではありません。", "利用者独自のCloudFrontをもう1段置く構成は追加設計です。本資料の標準には含めません。", "S05"),
R("独自CloudFrontを置く場合", "自分で案内窓口を追加するなら、取り次ぎ方も自分で決めます。", "既存要件が利用者管理distributionを指すなら、Cognito originとのHTTPS、POST/body/Authorizationの転送、Host、cache policyを別途設計します。", "token発行の共有cacheは使いません。Cognito管理distributionと同じ設定権限があると考えず、既存構成を確認します。", "S05 S38 S39"),
R("Cognito側WAFは別", "通行証窓口にも検査を置くなら、そちらにも規則を設定します。", "API Gatewayのregional WAFは、別のCognito token endpointを自動的に保護しません。Cognito User Poolにweb ACLを関連付ける機能は別設定です。", "M2Mが人用CAPTCHAを処理する前提にはしません。API用と認証用で許可・rate制御を設計します。", "S12 S40"),
R("ドメインの分離", "通行証窓口と本の注文窓口を区別します。", "auth.example.comはCognitoのtoken endpoint、api.example.comはRegional API、backend.example.comはALBとのTLS名/Hostの説明用です。", "同じAWSでも宛先・証明書・接続は別です。外部DNSからinternal ALBを公開入口にしません。", "S04 S05 S13"),
R("リージョンとAZ", "同じ地域に2つの校舎を用意します。", "例はap-northeast-1。A/Sで対応する物理AZにリソースを用意します。AZ-A/AZ-Bは説明用の呼称です。", "アカウントごとのap-northeast-1a等の文字が同じでも同じ物理AZとは限りません。AZ IDで照合します。", "S03 S16"),
R("業務VPC", "ロボットの入口と案内係を別区画に置きます。", "10.20.0.0/16内に、VPC Link ENI用、GWLBE用、ALB用、ECS用のサブネットを分けます。各役割を2AZに配置します。", "VPC LinkとALBを同一subnetにすると、subnet間ルートによる検査挿入の前提を満たしません。", "S15 S16"),
R("Security VPC", "検査だけを担当する敷地。", "10.80.0.0/16を例に、GWLB用、FWデータ用、FW管理用を分けます。GWLBとFWを同一subnetに置くことも製品仕様上は可能ですが、本例では分離します。", "FWから業務ALBへ直接出ていくルートは主経路にしません。検査後はGWLB/GWLBEへ戻します。", "S17 S21 S33"),
R("クロスアカウント接続", "本部が許した学校だけ専用の出入口を作れます。", "SがAの必要なprincipalにendpoint service接続権限を付け、必要に応じて接続要求を承認します。Aが自VPCでAZごとにGWLBEを作ります。", "GWLBはS、GWLBEはAです。VPC Linkが別アカウントのALBを直接選ぶ構成ではありません。", "S02 S16 S32"),
R("TGWの位置付け", "学校同士の大きな交差点が必要な場合に追加します。", "主構成は同一業務VPCのsubnet間をGWLBEへ向ける方式です。多数VPCをTGWで集約する検査パターンとは分けます。", "TGWを採用する場合はattachmentのappliance mode、TGWルート、AZ対称性も設計します。GWLBがあるだけでTGWが必須とはしません。", "S15 S19 S21 S56"),
R("何が資料外か", "地図にない道路は、必要なら別に設計します。", "ECSからDB、ECR、S3、CloudWatch、Secrets Manager等への接続、運用管理、DNS解決経路はこの業務要求とは別フローです。", "task起動やログ転送に必要なVPC endpoint/NAT等は別途用意します。APIの応答経路と混ぜません。", "設計範囲"),
])

section(6, "認証の行き帰り", "人のログイン画面を開かず、機械が通行証をもらう12段階です。ここではCognitoのカスタムドメインを使ったclient_credentialsを説明します。", [
R("A01 事前登録", "ロボット番号と合言葉、使ってよい部屋を登録します。", "User Poolにsecret付きapp clientを作り、client_credentialsと必要なcustom scopeを許可します。例はbooks-api/books.read。", "同じapp clientで人向けauthorization code/implicit flowと混在させません。", "S07 S08 S62"),
R("A02 DNSを調べる", "auth.example.comの窓口の場所を調べます。", "DNSレコードはCognitoが指定したCloudFront distributionのalias先へ向けます。クライアントは解決した入口へ接続します。", "DNSは住所を知らせる仕組みです。tokenそのものを運んだり検査したりしません。", "S05"),
R("A03 TLSで接続", "窓口との会話を鍵付きにします。", "クライアントがauth.example.comの証明書を検証し、CloudFront側のエッジとHTTPS接続を確立します。", "Cognitoカスタムドメイン用ACM証明書はUser Poolの場所にかかわらずus-east-1に用意します。", "S05"),
R("A04 tokenを要求", "合言葉を示して『読む通行証をください』と頼みます。", "POST /oauth2/token。Content-Typeはapplication/x-www-form-urlencoded。grant_type=client_credentialsとscopeを送り、client_secret_basic等でclientを認証します。", "BasicのBase64は暗号ではありません。HTTPSを維持し、secretをURIクエリに入れません。", "S06 S41"),
R("A05 エッジからCognito", "近くの窓口が事務室へ取り次ぎます。", "Cognito管理のCloudFrontを通してtoken endpointに要求が届きます。エッジ自体がclient secretの正否を最終判定してJWTを発行するわけではありません。", "要求ごとに異なる秘密を含むtoken発行応答を共有CDNキャッシュで配る設計にはしません。", "S05 S06 S39"),
R("A06 機械を認証", "登録番号と合言葉の組合せを確認します。", "Cognitoがapp client、secret、許可grantと要求scopeを確認します。M2MではユーザーパスワードやMFA入力を使う人の認証とは異なります。", "誤ったsecretや許可外scopeはtoken取得失敗として処理し、業務APIへ進めません。", "S06 S08"),
R("A07 JWTを発行", "期限付きで、まねできない印を付けた通行証を作ります。", "Cognitoはaccess tokenのclaimを作り、User Poolの署名鍵で署名します。機械のclient_id、token_use、scope、exp等が重要です。", "通常のclient_credentials応答はaccess tokenであり、ID token/refresh tokenは発行しません。", "S06 S09"),
R("A08 応答が戻る", "事務室→案内窓口→ロボットの順に通行証が戻ります。", "Cognitoのtoken応答がCloudFrontを経由してクライアントへ戻ります。JSONにはaccess_token、token_type、expires_in等が含まれます。", "この応答はALB/ECSへ向かいません。認証の往復はここで完了します。", "S05 S06"),
R("A09 安全に保管", "通行証を外へ見せず、期限内は使い回します。", "呼出側がtokenをメモリ等で保持し、対象scopeと期限を管理します。実装例として期限の少し前に再取得し、複数処理の同時更新を1回へまとめます。", "業務API1回につきtoken発行1回は必須ではありません。再利用と短い有効期限のバランスを取ります。", "S07 S09"),
R("A10 期限と再取得", "期限切れの通行証は新しくもらいます。", "M2Mにはrefresh tokenがないため、同じclient_credentialsでaccess tokenを取り直します。時計ずれや一時的な取得失敗も考慮します。", "401を見て無限に再取得せず、原因判別・回数上限・待ち時間を設けます。", "S06 S09"),
R("A11 secretを更新", "新しい合言葉へ、止めずに切り替えます。", "現在は同じapp clientに最大2個のsecretを保持できます。新secret追加→呼出側切替→確認→旧secret削除、という運用が可能です。", "旧secret削除と発行済みtoken失効は別です。緊急停止はtoken期限や追加拒否制御も考えます。", "S08 S57 S66"),
R("A12 新しい別方式", "最近は別の通行証窓口もあります。", "最新文書にはドメイン不要のGetClientToken APIもあります。client ID/secretでM2M tokenを得ますが、本資料のCloudFront経由/oauth2/tokenとは別経路です。", "『すべてのM2Mにドメイン必須』とは一般化しません。ユーザー指定の主経路は変えず、比較事項として扱います。", "S07 S31"),
])

section(7, "トークンの中身", "JWTは『内容を読める通行証に、改ざんを見破る署名が付いたもの』です。読めることと、信用できることは別です。", [
R("3つの部分", "表紙・説明文・本物の印。", "典型的な署名付きJWTはheader.payload.signatureという3部分です。headerにはalg/kid、payloadにはclaim、signatureには改ざん検出用の値があります。", "文字列をBase64URLデコードしただけでは検証完了ではありません。", "S09 S10 S42"),
R("iss：発行者", "どの事務室が作ったか。", "CognitoのissuerはUser Poolに対応するURLです。カスタムドメインのauth.example.comとtokenのissが必ず同じ文字列になるわけではありません。", "信頼したpoolのissuerだけを受け入れます。入力tokenが指定する任意URLへ鍵を取りに行く設計は避けます。", "S10"),
R("kidとJWKS", "印を見分けるための見本番号と見本帳。", "公開鍵集合JWKSからkidに対応した公開鍵を選んで署名を検証します。秘密の署名鍵はCognito側にあり、検証側は公開鍵で確かめます。", "鍵は変わり得ます。自作検証では信頼先固定、公開鍵キャッシュ、未知kid時の制御された再取得を設計します。", "S10"),
R("client_id / sub", "どのロボットの通行証か。", "M2M access tokenのclient_idはapp clientのIDです。現行文書ではsubも同じapp client IDとなり、人のユーザーIDではありません。", "M2M tokenにusernameやcognito:groups等の人向けclaimが必ずあると仮定しません。", "S09"),
R("token_use", "これはどの種類の通行証か。", "access tokenではtoken_use=access。ID tokenは人の属性を伝える目的で、access tokenはAPIの操作を許可する目的です。", "M2MのメソッドにはOAuth scopeを設定してaccess tokenによる認可を使います。", "S09 S11"),
R("scope", "図書室で『読む』ことだけ許す印。", "例はbooks-api/books.read。resource server identifierとscope名を/でつなぎます。複数scopeは通常スペースで区切られます。", "books.readとbooks-api/books.readは別文字列です。完全なscope名を一致させます。", "S07 S11"),
R("exp / iat", "いつ作られ、いつ期限が切れるか。", "expは有効期限、iatは発行時刻を表す時刻claimです。token検証は現在時刻との比較を含みます。", "サーバー時刻を同期し、呼出側は期限ぎりぎりまで待たず再取得します。例示の有効期間は設計値です。", "S09 S10"),
R("audの取り違え", "通行証の種類ごとに、書かれる欄が違います。", "通常のCognito M2M tokenをID tokenのaud前提で扱いません。現行Cognitoのresource bindingはユーザー向けで、client_credentialsには適用されません。", "REST Cognito authorizerのID token用aud正規表現をM2Mへ安易に設定しません。HTTP APIのaud/client_id規則とも区別します。", "S07 S10 S11"),
R("毎回Cognitoへ照会？", "印の見本があれば、その場で本物か調べられます。", "JWTは署名とclaimにより検証できる形式です。業務APIの呼出しごとに/oauth2/tokenへtokenを返して許可を聞く構造ではありません。", "公開鍵取得などの制御用通信はあり得ますが、業務のデータ経路とは分けて考えます。", "S10 S42"),
R("Bearerの性質", "持っている人が使える通行証です。", "一般的なBearer tokenは盗まれると、期限や権限の範囲で悪用され得ます。JWTの署名は盗難を防ぐ暗号化ではありません。", "TLS、秘密保管、ログの秘匿、最小scope、短命化を組み合わせます。", "S06 S41 S42"),
R("追加の業務権限", "図書室へ入れても、他の人の貸出記録を読んでよいとは限りません。", "scopeでメソッドを許可した後も、ECSアプリが対象データ、テナント、操作条件等を判断します。必要ならclient_idの許可リスト等も追加します。", "標準Cognito authorizerが任意claimの業務条件をすべて検証するとは扱いません。Lambda authorizerやアプリで補います。", "S07 S11"),
R("失効の限界", "新しい通行証の発行を止めても、配った通行証は手元に残ります。", "secret更新や削除は今後のtoken取得を制御します。すでに発行されたM2M JWTをローカルに検証する経路では、期限まで受け入れられることを前提に運用します。", "緊急遮断が必要なら追加の拒否リスト等を設計し、反映時間を実測します。", "S09 S66"),
])

section(8, "API受付と認可", "公開Regional REST APIの入口で何が起きるかを整理します。WAFとCognito authorizerは目的が異なり、両方を通った要求だけが後段へ進みます。", [
R("B01 新しいHTTPS要求", "通行証を持って、本の注文窓口へ行きます。", "クライアントはapi.example.comへ別のHTTPS接続を作り、GET /books/42とAuthorization: Bearer <access_token>を送ります。", "認証に使ったCloudFrontを、この業務要求も必ず通るわけではありません。主構成はRegional APIへ直接です。", "S06 S13"),
R("B02 WAFの判定", "注文用紙に危険な書き方がないか見ます。", "REST APIのstageに関連付けたregional web ACLが評価されます。WAFはresource policyやCognito authorizer等より先に適用されます。", "WAFでBlockなら後段のVPC LinkやFWへ要求を流さず拒否します。", "S12"),
R("本文サイズの限界", "大きな書類を、何ページまで調べるか決めます。", "API Gateway向けWAFのbody検査は既定16KB、設定で最大64KBです。検査上限を超える本文はoversize handlingに従います。", "『WAFが通ればすべての本文を検査済み』とは言えません。許容本文サイズ・超過拒否・後段検査を組み合わせます。", "S27"),
R("B03 APIのアクセス条件", "この入口を使ってよい場所や方法か確かめます。", "resource policy等を用いる場合は、その条件も要求に適用されます。WAF以外の全機能を固定の単純な直列装置として説明しません。", "IP制限、カスタムドメイン、default endpointの扱いを意図に合わせて設定します。", "S12 S13"),
R("B04 Cognito認可", "印・期限・『読む権利』を確かめます。", "RESTのCOGNITO_USER_POOLS authorizerをメソッドへ関連付け、OAuth scopeを設定します。scope未設定ではID tokenを使う動作となるため、M2Mの意図を設定に反映します。", "authorizerを作るだけで全メソッドが保護されるわけではありません。各メソッドへの関連付けが必要です。", "S11"),
R("scopeはOR条件", "この入口は『どれか1つの許可』があれば通れます。", "RESTメソッドに複数scopeを指定した場合、token内scopeのいずれかとの一致で許可されます。すべてのscopeを要求するAND条件ではありません。", "readとadminを両方必要にしたい場合、列挙だけでは不足です。追加の認可ロジックを設計します。", "S11"),
R("失敗を分ける", "通行証の問題と、道が壊れた問題を区別します。", "無効tokenやscope不一致は認可失敗、WAF拒否はWAF、後段の疎通やTLS失敗は統合の問題です。HTTPコードだけで発生箇所を決めつけません。", "エラー応答はカスタマイズで変わるため、request ID、WAFログ、APIログを突き合わせます。", "S11 S12 S35"),
R("認証テスト画面の注意", "練習窓口と実際の入口で、確認できることが違います。", "Cognito authorizerのコンソールtest invokeはID token向けで、access tokenを使う実メソッドのscope検証の代用になりません。", "M2Mはデプロイ済みstageの実URLにaccess tokenを付けて検証します。", "S11 S61"),
R("B05 統合へ渡す", "合格した注文を敷地内の案内係へ送ります。", "API GatewayはHTTP_PROXYのprivate integrationへ要求を渡します。APIメソッドのパス/ヘッダーとALBへ渡すHost/pathの設計を合わせます。", "secretは業務APIに渡しません。token/信頼済みclaimの後段転送方針は明示します。", "S02 S04"),
R("キャッシュと検査", "受付が控えの答えを返したら、図書室へは行きません。", "後段レスポンスをAPI Gateway等でキャッシュする設計では、cache hit時にVPC Link/ALB/FWへ進まない場合があります。", "今回の各呼出しをFWで検査する例は業務応答キャッシュ無効を前提にします。キャッシュ採用時は認可単位の分離も設計します。", "S39 S60"),
R("WAFは応答スキャナー？", "注文用紙を調べる係が、返す本の全ページも読むわけではありません。", "このWAF配置は受信HTTP要求の検査です。ECSが返す全応答本文をWAFが同じようにスキャンするというモデルではありません。", "戻りのネットワーク/本文検査はFWの対応機能・復号・ポリシーとアプリのデータ制御で考えます。", "S12 S27 S21"),
])
