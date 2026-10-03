from report_model import section, row as R

section(16, "TLSと検査範囲", "HTTPSは区間ごとの鍵付き通信です。『CloudFrontで暗号化した同じ箱がECSまで届く』という1本のTLS接続ではありません。どこで開けて、どこで再び鍵を掛けるかを整理します。", [
R("区間T0：認証", "ロボットと通行証窓口の間の鍵。", "クライアント↔CloudFrontがTLS接続です。CloudFrontからCognito側の処理はAWS管理です。利用者がCognito用distributionのorigin設定を自由に変えるモデルではありません。", "認証のsecretを保護する区間です。業務APIのTLSやGWLBE内の検査とは別です。", "S05 S06"),
R("区間T1：公開API", "ロボットと業務受付の間の鍵。", "クライアント↔Regional API GatewayでTLSを終端します。WAFがサービスからHTTP要求を受けて検査できるのは、この境界でHTTP内容を処理できるためです。", "WAFをTLSパケットの途中へIPルーティングで挿入する構造とは異なります。", "S12 S13"),
R("区間T2：統合", "受付からALBへの新しい鍵。", "API Gateway↔VPC Link↔ALBをHTTPSで設定します。GWLBE/GWLB/FWはそのIP経路上に入ります。TLS未復号なら本文とAuthorizationは暗号化されています。", "GWLBEを通ること自体は暗号化解除の条件になりません。", "S02 S04 S17"),
R("区間T3：task", "ALBから実際の担当者への、さらに別の鍵。", "ALBでT2が終わり、ALB↔ECSへHTTPまたはHTTPSの独立した接続を作ります。本資料の例はHTTPS 8443を採用し、task側の証明書も準備する前提です。", "ALBのHTTPS target接続はtarget証明書を検証しない仕様です。暗号化と相手証明書の検証を同一視しません。", "S25 S64"),
R("案A：TLSを通過", "鍵付きのまま、宛先や荷物の流れを調べます。", "FWはIP/port、セッションの状態、暗号化されていないTLS情報など取得可能な情報で制御します。HTTP本文、tokenの中身、暗号化されたURLは読めません。", "『本文まで脅威検査』が必須なら、この案だけでは要件不足です。見える情報はTLS仕様や設定にも依存します。", "S21 S22"),
R("案B：Inbound復号", "検査所で箱を開け、調べた後に再び鍵を掛けます。", "FWに対象サーバーの証明書と秘密鍵を用意し、SSL Inbound Inspectionとsecurity profileを設定します。API Gatewayが接続先の証明書名・信頼を確認できることが必要です。", "本番採用候補として、TLS版、cipher、PAN-OS/plugin、証明書更新、負荷、例外通信を実機で検証します。", "S04 S21 S22"),
R("証明書の入手", "検査員が正しい鍵を持てるかを先に確認します。", "ACM public certificateにはexportableとして発行する選択肢があります。2025-06-17以前の証明書や非exportable設定を、当然に取り出せるとは扱いません。", "新規exportable証明書または適切なimport証明書等を選び、FWへの鍵配布と更新を設計します。秘密鍵は資料へ記載しません。", "S23 S67"),
R("Forward Proxyとの違い", "検査員が別の名札を作る方式とは、必要な準備が違います。", "SSL Forward Proxyは検査側CAをクライアントに信頼させる方式が基本です。API Gatewayのmanaged integrationでその信頼関係が成立するかを別途確認する必要があります。", "独自CAを使い、TLS検証を無効化して通すことを解決策にしません。ここではInbound方式を検討の中心にします。", "S04 S22"),
R("案C：統合をHTTP化", "鍵を掛けずに送れば検査所は本文を読めます。", "API Gateway→ALBがHTTPならFWで本文を扱いやすくなりますが、tokenや本文がその区間で平文になるという設計変更です。", "PrivateLinkやGENEVEという名前だけでアプリの平文を暗号化済みと説明しません。機密性要件に照らして判断します。", "S02 S17"),
R("token検証と復号", "箱を開けられることと、通行証が本物か判断することは別です。", "復号でtoken文字列が見えても、FWが自動的にCognitoのscope認可を代替するわけではありません。API Gatewayの認可、FWの脅威検査、ECSの業務権限を分けます。", "復号ログやpacket captureへsecret/token/個人情報を残さないように制御します。", "S11 S21 S22 S36"),
R("ALBの追加JWT検証", "案内係でも通行証をもう一度確認できます。", "現在のALBにはHTTPS listenerでJWTを検証する機能があります。iss/exp/署名、必要な追加claimを検証でき、Cognito M2Mとの二重チェックを構成可能です。", "authenticate-cognitoの対話型ログインとは別機能です。RS256、公開JWKS等の制約を確認します。本例では任意の追加防御です。", "S29 S30"),
R("復号の完了条件", "箱を開けた証拠と、危険な荷物を止めた証拠の両方を確認します。", "許可された検証用通信に対し、FWの復号結果、適用rule、復号失敗の原因、脅威テストの期待動作を照合します。HTTPS成功だけでは本文検査成功を証明しません。", "証明書更新後・スケール後・AZ切替後も確認します。結果は未実施/成功/失敗を分けて記録します。", "設計上の検証・S21 S22"),
])

section(17, "SGと許可設定", "次はIPv4・HTTPS統合・SNATなしという設計例です。厳密なルールは実CIDR、ポート、FW構成に合わせます。ルート、SG、NACL、FWポリシーはそれぞれ別に必要です。", [
R("Link側SGの送信", "受付の出口は、ALBの区画へだけ送り出します。", "VPC Link ENIのSG outboundでALB-A/B subnet 10.20.30.0/24、10.20.31.0/24へのTCP443を許可する例です。", "ALBの動的IP1個に固定せず専用subnet単位で管理します。不要な全宛先許可を初期値のまま残しません。", "設計例・S03 S15"),
R("ALB側SGの受信", "案内係は受付の出口から来た注文を受けます。", "ALB SG inboundはLink-A/B subnet 10.20.10.0/24、10.20.11.0/24からのTCP443を許可する例です。", "middlebox経由の通信では対向SG参照が期待どおり機能しない制約があります。本例はCIDRで明示します。", "S15"),
R("SGだけでは検査保証不可", "名札が合っていても、どの道を通ったかは別です。", "透過FWは内側の送信元IPを保つため、ALBのCIDR許可だけでは『必ず検査済み』を証明できません。経路の制御と変更権限の管理が必要です。", "専用Link subnetに別の送信元を勝手に作らせない運用、route変更監視、迂回テストを組み合わせます。", "設計上の推論・S15 S21"),
R("ALB→ECSのSG", "図書室の担当者は案内係からだけ注文を受けます。", "本例の直接ALB→task区間ではtask SG inboundをALB SGからのTCP8443に限定できます。ALB outboundとhealth checkも整合させます。", "将来この区間にもmiddleboxを入れる場合は、SG参照の扱いを再検討します。", "S15 S24 S25"),
R("GWLBにはSGを付けない", "配分係ではなく、検査員の入口を制限します。", "GWLB自体に関連付けるSGではなく、FWのデータENI側SGでGENEVEの受信と応答、health checkを許可します。", "GWLBノードのsubnet/IP範囲を送信元にします。ALBのようにGWLB SG参照を作る前提にしません。", "S33 S68"),
R("FWのGENEVE許可", "検査用の袋を受け取る専用窓口。", "例ではGWLB subnet 10.80.10.0/24、10.80.11.0/24とのUDP6081をFW側で扱います。検査後のGENEVE応答と設定済みhealth portも必要です。", "実際のsource/destination、FW interface、health check portは採用テンプレートと機種設定で確認します。", "S21 S33 S63"),
R("GWLBEの制御", "検査所への出入口を誰が接続できるか決めます。", "GWLBEはInterface endpointと同じSG設定画面を使う前提にしません。endpoint service権限・接続承認、subnet経路/NACL、送受信ENIのSGで制御します。", "S3/DynamoDB向けGateway endpointのpolicyを、そのまま検査用GWLBEへ当てはめません。", "S16 S32 S34"),
R("NACLの往復", "行きと帰りの門番へ、両方の通行条件を伝えます。", "NACLはstateを持たないため、TCP443/8443の要求だけでなく戻りのephemeral port等も許可します。FW subnetは外側GENEVEを扱います。", "全subnetで6081だけを開ければよいわけではありません。元通信とカプセル化通信の場所を区別します。", "S16 S18 S33"),
R("FWポリシー", "本当に何を許すかは検査員の規則で決めます。", "Link→ALBの必要サービス、zone、source/destination、復号、security profile、ログ設定を定義します。管理通信は業務データの許可と分離します。", "UDP6081をAWS SGで許しても、内側のHTTPSや業務アプリがFWで許可されたことにはなりません。", "S21 S22 S63"),
R("secretと変更権限", "合言葉を管理する人と、道を書き換える人を制限します。", "client secret、証明書秘密鍵、FW管理権限、route変更権限を必要な担当へ限定します。endpoint serviceの接続許可は対象principalを絞ります。", "機密値をExcelやMarkdownへ実値で埋め込みません。資料は名称・参照方法・責任者を記載する場です。", "S08 S22 S32"),
])

section(18, "ALBとECS", "ALBは通信をそのまま1本の管でECSへ通すのではなく、HTTPを受けて担当taskへ別接続で届けます。そのためIP、TLS、戻り道の理解が変わります。", [
R("internal ALB", "学校の中にだけいる案内係。", "schemeはinternalとし、インターネットからALBへ直接来る入口は主構成に置きません。VPC Linkからの到達を設計します。", "DNS名が分かることと、インターネットから接続できることは別です。", "S02 S04"),
R("Hostとpath", "注文の宛先名と種類を見て机を選びます。", "API Gatewayの統合URI、ALB listenerのHost/path条件、ECSアプリのURLを一致させます。stage付加やHost変更も含めて設計します。", "TLS成功後の404はnetwork障害ではなく、rule/pathの不一致である可能性があります。", "S02 S04 S25"),
R("taskの登録", "勤務中の担当者の名簿を自動更新します。", "ECS serviceが起動/終了するtaskをALB target groupへ登録・解除します。awsvpcではtask ENIのIPをtargetに使います。", "ip target typeを選び、task IPを手作業で固定登録する運用に依存しません。", "S24"),
R("health check", "担当者が仕事を受けられるか、定期的に確認します。", "ALBはtaskへhealth checkを行います。これはVPC Link→ALBとは別通信です。今回のFW挿入を経由するとは限りません。", "正常なhealth checkは、外部API→認可→FW→ALB全経路の正常性を証明しません。", "S24 S25"),
R("task起動とreadiness", "担当者が席に着くまで待ってから仕事を渡します。", "アプリ起動、health endpoint、ECSのgrace period、ALB target状態の設計を合わせます。更新時は終了中taskへの接続も考慮します。", "FWのhealthyとALB targetのhealthyは別指標です。", "S24 S37"),
R("taskから見えるsource", "担当者が直接話している相手は案内係です。", "taskのTCP相手はALBです。外部クライアントIPをネットワークsourceだけから取り出せるとは限りません。HTTP転送ヘッダーを別途扱います。", "Palo Altoが見るT2のsourceはVPC Link側。『元IP維持』はAPI Gatewayより外側までさかのぼる意味ではありません。", "S03 S26 S64"),
R("X-Forwarded-For", "注文用紙に前の窓口の情報が追記されます。", "ALBは設定に従ってX-Forwarded-For等を処理します。外部クライアントが任意に指定した値も混ざり得るため、無条件で先頭値を本人のIPと信じません。", "信頼するproxy段数・上書き方針を定義し、API GatewayのsourceIp等の信頼済み情報との対応を確認します。", "S26 S35"),
R("業務認可の場所", "どの本を誰へ渡してよいかは図書室でも判断します。", "API Gatewayのscopeで入口を許可し、アプリで対象リソースの権限やテナント分離を確認します。必要に応じてJWTを独立に再検証します。", "clientが自作できるヘッダーだけを、検証済みidentityとして信頼しません。", "S07 S10 S11"),
R("ALBのJWT再確認", "案内係にも確認を任せる選択肢があります。", "verify JWT機能を追加するなら、issuer、公開JWKS、必須claim、追加claimの条件をAPI認可と一致させます。", "追加しただけで自動的に同じポリシーになるわけではありません。二重設定のずれもテストします。", "S29"),
])

section(19, "可用性と性能", "部品が複数あると、遅延・コスト・障害点も増えます。必要な保護を維持しながら、どの区間で何を測るかを決めます。", [
R("2AZの意味", "校舎が1つ使えなくても、別の校舎で新しい仕事を受けます。", "Link ENI、GWLBE、ALB、ECS、GWLB/FWを対応する2AZへ配置します。各AZで必要なFW容量を確保します。", "冗長配置だけで既存TCP接続が無停止で移るとは言えません。復旧は新規要求と既存要求を分けて測ります。", "S03 S16 S19 S24"),
R("FWの能力", "検査員の数だけでなく、荷物の難しさでも処理量が変わります。", "帯域、同時session数、新規接続数、TLS復号、脅威防御、ログ出力がFW負荷へ影響します。", "『ネットワーク帯域だけ十分』では不足です。実際のTLS/本文サイズ/接続再利用を再現して試験します。", "S18 S21 S22"),
R("GWLBとFWの増加", "配分係が増えても、検査員が自動で増えるとは限りません。", "GWLBのサービス側スケールと、VM-Series EC2群のスケールは別の管理事項です。新規FWの起動・設定・health check・licenseが整ってから利用します。", "スケール時間と急増時の余裕を見積もります。", "S17 S20 S21"),
R("遅延を分ける", "通行証の取得時間と、本を探す時間を分けて測ります。", "認証の往復はtoken再取得時、通常APIはWAF/認可＋private integration＋検査＋ALB＋アプリの時間を含みます。", "毎回tokenを取得して測ると、API自体の応答時間との比較ができません。p50/p95/p99等で区分します。", "設計上の測定・S07 S35"),
R("跨AZの代償", "遠い校舎へ往復すると時間と運賃が増えます。", "Link-A→ALB-Bのような接続を許す設計ではAZ間転送を含みます。同じendpointへ戻す対称性を優先した上で、実トラフィックと費用を評価します。", "『同じAZのALBに必ず接続される』という未確認の前提でルートを省略しません。", "設計上の推論・S16 S18"),
R("timeoutの整合", "受付、案内係、担当者で待てる時間を合わせます。", "client、API統合、ALB、FW/TCP session、アプリの各timeoutとkeep-aliveを確認します。短い側から接続が切れ、再利用時の失敗につながる場合があります。", "古い『API Gatewayは常に29秒で固定』等を一般化せず、endpoint種別・quota・転送modeを確認します。", "S18 S19 S60"),
R("BUFFEREDとSTREAM", "全部そろえてから渡すか、できた分から渡すか。", "主説明は通常のBUFFERED応答です。現在のRESTはHTTP_PROXY private integrationでresponse streamingも利用可能です。", "STREAMはcache/変換等の対応範囲が異なります。長い応答に採用するならtimeout、FW、ALB、clientを別に試験します。", "S60"),
R("tokenの再利用", "同じ期限内の通行証を大切に使います。", "client_credentialsの取得回数を必要範囲へ抑えると、token発行の負荷と待ち時間を削減できます。", "更新の集中を避け、期限前の少しずれた再取得と上限付きretryを設計します。", "S07"),
R("費用の主な要素", "窓口代、通路代、検査員代、荷物の運賃を分けます。", "CognitoのM2M利用、API Gateway要求、WAF、ALB、GWLB/GWLBE、VM-Series/EC2、転送、ログ等を項目別に見積もります。単価と適用条件は契約・Region・最新料金で再確認します。", "本資料は料金見積書ではありません。要求数、token発行数、bytes、AZ経路、常時台数を入力条件にします。", "設計上の見積項目・S07 S16 S27"),
R("検査の共有と影響範囲", "本部に検査を集めると統一しやすい一方、多くの学校が本部に依存します。", "複数アカウントでFWのpolicy/監視を集約できますが、設定ミスや容量不足の影響が広がり得ます。", "アカウント/用途ごとのpolicy分離、段階的更新、容量監視、復旧手順を準備します。", "S21 S32 S56"),
R("IPv6を使う場合", "別の住所の書き方にも道しるべを用意します。", "本表のIPv4 /24ルートだけではIPv6経路を規定しません。API、Link、ALB、GWLBE、FWの対応範囲とIPv6ルート・許可をそろえます。", "IPv4だけ検査しIPv6が別経路を通る状態を避けます。GWLBEとegress-only IGWの制約も確認します。", "S03 S15 S16"),
])

section(20, "ログと障害調査", "『最後に成功した場所』と『最初に届かなかった場所』を探します。HTTPコードだけでなく、複数のログを同じ時刻と識別子で照合します。", [
R("相関させる情報", "注文番号と時刻を各窓口で記録します。", "UTC時刻、API request ID、method/path、許可された識別情報、status、処理時間をそろえます。FWは5-tuple/session ID、ALBはtarget/status等で補完します。", "1つのIDがすべての装置へ自動伝播するとは限りません。アプリへの信頼できる相関ID伝播を設計します。", "S35 S36 S37"),
R("token取得失敗", "通行証が出なければ、図書室の道を調べる前に窓口を調べます。", "DNS/TLS、client ID/secret、grant、scope、Cognito側のWAF等を確認します。secret値そのものをログへ出さず、エラー分類を記録します。", "token取得失敗時にALBやGWLBEを変更しても原因が解決しない場合があります。", "S06 S08 S40"),
R("WAFで拒否", "受付で注文が止まっています。", "WAFログのterminating ruleやactionと、対象stage/web ACLを確認します。例外ルールを広げる前に誤検知か意図した拒否かを調べます。", "正しいtokenがあることはWAF許可の条件を代替しません。", "S12 S27"),
R("認可で拒否", "通行証の期限か、使える部屋が違います。", "issuer、token種別、期限、要求scope、メソッドauthorizer関連付け、stageへのデプロイを確認します。", "外部のJWT解析サイトへ本番tokenを貼り付けません。安全なローカル手段で必要claimのみ確認します。", "S09 S10 S11 S61"),
R("API 5xx / timeout", "受付から奥へのどこかで返事が途絶えています。", "統合ログ、VPC Link状態、ENIの空きIP、ALB listener/TLS、往復ルート、SG/NACL、FWのdropを順に切り分けます。", "5xxをすべてECSの障害と判断しません。FW dropはtimeoutとして現れることもあります。", "S03 S04 S35 S37"),
R("一部AZだけ失敗", "片方の校舎の道しるべが欠けているかもしれません。", "4組合せのLink/ALB subnetルート、endpoint状態、物理AZ ID、FW target状態を比較します。", "APIのDNS結果やALBノードが変わっても検査が成立することを確認します。", "S15 S16 S20"),
R("FWに行きしかない", "帰りの荷物が同じ検査所へ来ていません。", "ALB→Link CIDRルートの欠落、別endpoint選択、FW stateやNAT、戻りNACLを調べます。", "最初からFWの許可を広げず、対称性を先に確認します。", "S15 S19 S21"),
R("FWに通信がない", "検査所に立ち寄っていないか、そこまで届いていません。", "API/WAF/authorizerでの拒否、キャッシュ、Link→ALBのlocal直行、endpointの未承認等を順に確認します。", "正常応答があるのにFW記録がない場合も『検査正常』とは報告しません。", "S12 S15 S16 S39"),
R("ALBには届くが404", "道は合っていても、注文の机が違うかもしれません。", "統合URIのHost、stage付加、ALBのpath/host rule、ECSアプリのrouteを照合します。", "ALB固定応答とtaskの404をALBログで区別します。", "S02 S04 S37"),
R("taskがunhealthy", "担当者がまだ準備中か、検査用の質問に答えられていません。", "target type、container port、health path、SG/NACL、起動時間、taskログを確認します。", "ALB health checkはAPI Gateway/Cognitoを通らないため、認可済み業務APIだけでhealthを定義しないよう配慮します。", "S24 S25 S37"),
R("復号失敗", "検査所が箱の鍵を開けられていません。", "対象証明書と秘密鍵、更新済み証明書の配布、SNI/Host、TLS版/cipher、PAN-OS/plugin、FW復号policyを確認します。", "『通過したので復号済み』と判定せず、復号失敗時に許可/遮断のどちらになるかも確認します。", "S04 S21 S22 S23"),
R("VPC Flow Logsの限界", "交通量の記録は、荷物の中身の検査記録ではありません。", "Flow Logsは通信のメタデータや許可/拒否等の調査に使います。APIのscope判定や本文脅威検査の代わりにはなりません。", "FW通過はFWログ、HTTP結果はAPI/ALB/アプリログと組み合わせます。取得対象や記録されない通信も確認します。", "設計上の観測・S21 S35"),
R("秘匿したログ", "注文の記録を残しても、合言葉を掲示板に貼りません。", "Authorization、client secret、token応答、復号本文、個人情報の保存を最小化します。API execution loggingでもdata tracingは機密情報を含み得ます。", "保持期間、閲覧権限、マスク、暗号化、調査用captureの扱いを運用設計へ含めます。", "S36"),
])
