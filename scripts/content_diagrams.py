from report_model import section, row as R

ARCHITECTURE = r'''flowchart TB
  subgraph AUTH["I. トークン取得：業務APIとは別の往復"]
    C0["M2Mクライアント"] <-->|"HTTPS /oauth2/token・JWT応答"| CF["グローバルエッジ CloudFront\nCognito管理"]
    CF <-->|"AWS管理の取り次ぎ"| COG["Cognito User Pool\nclient認証・scope・署名"]
  end
  subgraph FRONT["II. 業務要求：AWSマネージドサービス側の入口"]
    C["同じクライアント\n取得済みtokenを付ける"] <-->|"新しいHTTPS接続"| API["Regional REST API / API Gateway\nWAF → Cognito authorizer"]
  end
  subgraph A["業務アカウントA / 業務VPC 10.20.0.0/16"]
    L["VPC Link V2 ENI\n専用Link subnet"]
    E["GWLBE\n専用Endpoint subnet"]
    ALB["internal ALB\n専用ALB subnet / HTTPS終端"]
    TASK["ECS task\n専用Task subnet / 業務処理"]
    L <-->|"/24の往復ルート"| E
    E <-->|"検査済み要求・応答の検査"| ALB
    ALB <-->|"別のTCP/TLS接続"| TASK
  end
  subgraph S["検査アカウントS / Security VPC 10.80.0.0/16"]
    G["GWLB + endpoint service"]
    P["Palo Alto Networks VM-Series\n許可・遮断・必要に応じTLS復号"]
    G <-->|"GENEVE / UDP 6081"| P
  end
  API <-->|"private integration"| L
  E <-->|"AWS PrivateLinkによる検査の往復"| G
  classDef mono fill:#eeeeee,stroke:#444444,color:#111111;
  class C0,CF,COG,C,API,L,E,ALB,TASK,G,P mono;
'''

SEQUENCE = r'''sequenceDiagram
  participant C as M2Mクライアント
  participant CF as CloudFront
  participant Cog as Cognito
  participant API as Regional REST API
  participant L as VPC Link ENI
  participant E as GWLBE
  participant G as GWLB
  participant F as VM-Series
  participant A as ALB
  participant T as ECS task
  C->>CF: POST /oauth2/token (client credentials)
  CF->>Cog: token発行要求
  Cog-->>CF: access token
  CF-->>C: access token / expires_in
  Note over C,API: ここから別の業務HTTPS要求
  C->>API: GET /books/42 + Bearer token
  API->>API: WAF → Cognito authorizer / scope
  API->>L: HTTPS private integration
  L->>E: ALB subnet宛て /24 route
  E->>G: 検査サービスへ
  G->>F: GENEVEで元パケットを転送
  F-->>G: 許可パケット（必要なら復号検査）
  G-->>E: 元のGWLBEへ返却
  E->>A: 検査済み要求をALBへ
  A->>T: 別のTCP/TLS接続で処理依頼
  T-->>A: HTTP応答
  A->>E: Link subnet宛て /24 route
  E->>G: 戻りも同じGWLBEから検査
  G->>F: 同じフローの担当FWへ
  F-->>G: 許可された戻りパケット
  G-->>E: 元のGWLBEへ返却
  E-->>L: local routeでLink ENIへ
  L-->>API: 統合応答
  API-->>C: 業務HTTP応答
  Note over L,A: 往復の検査対象はLink↔ALB区間
  Note over A,T: ALB↔taskは独立した接続
'''

section(2, "全体構成図", "CloudFrontは認証の入口。公開Regional APIは利用者VPCの外側にあるサービスの入口。VPC Linkから先で、別アカウントの検査サービスを往復します。", [
R("図の読み方", "2つの往復を別々にたどります。", "Iでtokenがクライアントへ戻った後、IIを開始します。検査の寄り道は必ずGWLBE→GWLB→FW→GWLB→元のGWLBEです。", "図の双方向矢印は到達関係。時間順序は03章を参照。AZ-Aの経路を代表表示し、Bにも同じ役割を配置します。", "S02 S05 S15 S17"),
R("IGWを置かない理由", "町の窓口への来客は、学校の門を通る必要がありません。", "公開Regional API Gatewayへインターネットから入る位置に、利用者のIGWはありません。VPCへ入るのはprivate integrationのVPC Link側です。", "ALBとECSの応答もVPC Link→API Gatewayへ戻ります。", "S13 S14"),
R("設計例の確認範囲", "地図どおりの道を、現地で確かめる必要があります。", "同一業務VPCでVPC Link ENIとALBを別subnetに置き、GWLBEをmore specific routingで挿入する、公式機能を組み合わせた参照設計です。", "この特定の組合せのAWS/PAN-OS実機動作・性能・復号は未確認。14・23章を使って受入検証します。", "設計上の統合・S03 S15 S21"),
], kind="architecture")

sequence_rows = [
("01 / T0", "クライアント → CloudFront", "POST /oauth2/token。client ID/secretと必要scopeを送ります。", "TLS接続T0：secretを保護。", "S05 S06"),
("02 / T0", "CloudFront → Cognito", "Cognitoへtoken発行を取り次ぎます。", "CloudFront自体がJWT発行者ではありません。", "S05 S06"),
("03 / T0", "Cognito → CloudFront", "client認証・scope確認後、署名済みaccess tokenを返します。", "通常のM2MにID/refresh tokenはありません。", "S06 S09"),
("04 / T0", "CloudFront → クライアント", "tokenを受け取り、安全に保持します。", "認証の往復はここで完了。", "S05 S06"),
("05 / T1", "クライアント → Regional API", "新しい要求へBearer tokenを設定します。", "業務用HTTPS接続。Cognito用CloudFrontとは別。", "S11 S13"),
("06 / 処理", "API内：WAF → 認可", "WAF、Cognito authorizerとscope条件を満たすか確認します。", "拒否ならここで応答。後段へ進みません。", "S11 S12"),
("07 / T2", "API → VPC Link ENI", "ALB向けprivate integrationの接続を作ります。", "外部client接続とは別の通信。", "S03 S04"),
("08 / T2", "Link ENI → GWLBE", "ALB subnet /24へのルートを使います。", "source例10.20.10.10。", "S15"),
("09 / 検査", "GWLBE → GWLB", "アカウントSの検査サービスへ送ります。", "PrivateLinkの検査用往復。", "S16 S17"),
("10 / 外側", "GWLB → VM-Series", "GENEVEで包み、担当FWへ渡します。", "外側UDP6081／内側TCP443。", "S63"),
("11 / 外側", "VM-Series → GWLB", "許可した要求パケットを返します。", "FWの設定に従い検査・必要な復号。", "S21 S22"),
("12 / 検査", "GWLB → 元のGWLBE", "検査済み要求を元の業務VPCへ返します。", "FWからALBへ直接抜けません。", "S17 S21"),
("13 / T2", "GWLBE → ALB", "Endpoint subnetのlocal routeでALBへ届きます。", "ALBでT2を終端。", "S15 S64"),
("14 / T3", "ALB → ECS task", "別の接続でHTTP要求を渡します。", "本例HTTPS8443。今回のGWLBE区間外。", "S24 S25"),
("15 / T3", "ECS task → ALB", "業務結果を同じbackend接続で返します。", "外部clientへ直接応答しません。", "S25 S64"),
("16 / T2", "ALB → GWLBE", "Link subnet /24の戻りルートで送ります。", "往路と同じendpointを選択。", "S15 S19"),
("17 / 検査", "GWLBE → GWLB", "応答も検査サービスへ送ります。", "往復対称性を維持。", "S17 S19"),
("18 / 外側", "GWLB → 同じVM-Series", "同じフローの状態を持つFWへ送ります。", "通常のflow stickiness。障害時は別途考慮。", "S19 S20"),
("19 / 外側", "VM-Series → GWLB", "許可した応答パケットを返します。", "本文の可視範囲は復号設定によります。", "S21 S22"),
("20 / 検査", "GWLB → 元のGWLBE", "応答を元のendpointへ戻します。", "インターネットへ直接出ません。", "S17"),
("21 / T2", "GWLBE → VPC Link ENI", "Endpoint subnetのlocalでLink ENIへ届きます。", "例10.20.30.10:443→10.20.10.10:53000。", "S03 S15"),
("22 / 統合", "VPC Link → API Gateway", "統合接続上の応答をAPIが受け取ります。", "認証サービスへの再照会ではありません。", "S02 S03"),
("23 / T1", "API Gateway → クライアント", "公開HTTPS接続上で業務結果を返します。", "Cognito・認証用CloudFrontは通りません。", "S13"),
]
section(3, "往復シーケンス", "T0=認証、T1=公開API、T2=API統合、T3=ALB→task。T0/T1/T2/T3は別の接続です。GENEVE外側の通信がT2を包むので、同じポートと勘違いしないようにします。", [R(*r) for r in sequence_rows], kind="sequence")
