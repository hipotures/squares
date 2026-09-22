# 手法の先行研究と我々の寄与の切り分け（2026-09-15 調査）

## 結論: 手法の6要素はすべて既存。新規性は n ≥ 22 への初適用のみ。

| # | 要素 | 判定 | 初出 |
|---|---|---|---|
| 1 | 重み付き分数 unavoidable set | **既存** | Göbel → Stromquist（重み1、1984 memo / 2003 EJC）→ **Nagamochi 2005**（最初の重み付き。点・線分・面積のスコア、手調整、LP なし）→ **Sam Burns 2026-08**（最初の純粋な分数版。n=17、268 原子、質量 16.9476） |
| 2 | D4 対称性 | **既存** | この分野の標準。Burns–Massaccesi の Condition 1 に明記。jlevy は列生成で D4 軌道として使用 |
| 3 | 縮小 B<1 + 有限有理方向ネット、B(1+D)<1 | **既存（最重要）** | **Burns 2026-08** が厳密有理方向ネットの枠組みを構築。**Massaccesi 2026-08** が `cos ε + sin ε ≤ 1+ε ≤ 1+D` を181方向・B=0.9973 で明記。jlevy の Condition 3/4 は Burns–Massaccesi の再述で、出典を明示している。我々の B=0.9977・201方向はパラメータ変更にすぎない。縮小自体はさらに古く Stromquist の箱のトリックで、Nagamochi と Bentz 両論文も同じものを使う |
| 4 | 被覆LP + 行生成 | **既存** | Massaccesi が最初に LP で重みを求めた（行は固定）。**jlevy/squares** が分離オラクルによる行生成・切除平面ループを追加。TUTORIAL.md に文書化 |
| 5 | 双対価格による列生成 | **既存** | **jlevy/squares**。双対の `depth_y(x) ≤ 1` による被約費用判定で原子軌道を追加。n=19 の 24/5 証明書は「単一の再開列生成実行」と記録 |
| 6 | 分枝限定を分離オラクルに | **既存** | **jlevy/squares**。`sqpack.fractional.certificate.py` が区間分枝限定を Condition 5 の第二の判定器として実行。なお彼らの event-cell sweep は箱の分枝限定より強く、連続体の真の最小値を厳密に決定する |
| — | 中規模 n（26, 29, 39, 40） | **新規** | 分数証明書が n ≥ 22 で試みられたことは一度もない |

## 我々の以前の認識の誤り
「既存手法は n ≤ 22 か 13/22/33/46 の特定ケースに限られる」は**不正確**だった。
実際の分数証明書のフロンティアは以下の通り:
- Burns: n=17 (4.4811)
- Massaccesi: n=17, 18, 19 (4.5058)
- jlevy/squares: n = 11, 12, 17, 18, 19, 20, 21（T-017〜T-021）。s(21) ≥ 24/5、s(20) ≥ 97/20 を含む
- anabologyco-maker: n=17 (4.5705)、Lean 4 の `native_decide` 層つき

## それでも新規性が残る理由
jlevy の `packing/frontier/n-0{26,29,39,40}.md` を直接確認したところ、4件すべてで
**独立に検証された下界は Nagamochi 2005 の閉じた式のみ**である:
- n=26: 5.1231、n=29: 5.4721、n=39: 6.2915、n=40: 6.4031

Green 2000 の値（5.3918、5.5117、6.3506、6.3852）は DS7 の Theorem 9/10 経由の私信で、
**証明は一度も回収されていない**。我々の4件はこの空白に入る。

## 受けた警告と、その検査結果
jlevy は手法の**天井**を証明している。ネットのパラメータ D に対し、証明書は
`⌈√n⌉/(1+D)` を超えて存在できない。また経験的に、n が 20 前後で被覆値が天井より
ずっと下で縛られ、LP が退化した頂点（⌈√n⌉² 個の単位重みの双対解）に固定される
現象が観測されている。n=26, 39, 40 はより大きい領域なので、この退化がより強く効く恐れがある。

**検査結果（2026-09-15）: 4件とも退化ではない。**

| n | L | 質量 | ⌈√n⌉² に張り付き | 天井 ⌈√n⌉/(1+D) | L は天井以下 |
|---|---|---|---|---|---|
| 26 | 5.45 | 25.855744 | 否（36 ではない） | 5.987576 | はい |
| 29 | 5.57 | 28.992704 | 否 | 5.987576 | はい |
| 39 | 6.50 | 38.519038 | 否（49 ではない） | 6.985505 | はい |
| 40 | 6.50 | 39.000796 | 否 | 6.985505 | はい |

## 論文に書くべき先行研究への言及（推奨文案）
> We apply the weighted fractional unavoidable-set certificate method of Burns and
> Massaccesi (2026), which fractionalizes Stromquist's unavoidable point sets (1984/2003)
> and descends from Nagamochi's (2005) weighted point/segment/area score systems and
> Bentz's (2010, 2016) refinements. Following Burns and Massaccesi we reduce orientations
> via D4 symmetry and a rational direction net with the shrink condition B(1+D) < 1.
> Following the generator described in jlevy/squares (2026) we search for certificates by
> a covering LP with row and column generation and verify Condition 5 by interval branch
> and bound. Our contribution is the first application of this method to n ≥ 22,
> specifically n = 26, 29, 39, 40, where the only previously verified lower bound is
> Nagamochi's closed form and where Green's (2000) reported bounds rest on an unrecovered
> private communication.

## 追加すべき引用
- Stromquist, *Packing 10 or 11 Unit Squares in a Square*, EJC 10 (2003) #R8、および未公刊の 1984–85 memo I–III
- Nagamochi, EJC 12 (2005) #R37
- Bentz, EJC 17 (2010) #R126
- Bentz, arXiv:1606.03746（Theorem 8 の「連続変化する族」は連続性・位相的議論であり、
  **緩和ではない**。我々の分数化の祖先ではない点に注意）
- Friedman DS7
- Burns および Massaccesi のブログ記事
- jlevy/squares リポジトリ
- Bašić–Slivková, *On optimal piercing of a square*, Discrete Appl. Math. 247 (2018) 242–251（transversal の枠組み）

## 円詰め込みとの対比（論文に使える枠組み）
Markót–Csendes は純粋な区間分枝限定で n=28, 29, 30、のち 31–33 の円を各20〜50 CPU時間で解いた。
これは配置空間を**直接**厳密に排除する方法である。我々の手法は**双対証明書**であり、
配置空間を探索せずに済ませる。回転を許す単位正方形では、直接の区間分枝限定は n=3 にしか到達していない。
この対比は正当な論点になる。

## 次の方向（手法としての寄与を狙う場合）
jlevy は点原子を超えて **threshold atoms** に進んでおり（T-025/T-026、s(11) ≥ 191/50）、
これは点原子の天井を証明可能に破る。手法としての持続的な寄与を狙うならここが開かれた地面である。

## 調査の留保
1. Burns の証明ノート本文は取得できず、ブログ要約のみ。Burns と Massaccesi の
   クレジット配分は Massaccesi 自身の帰属と jlevy の監査に依拠している。
2. 分数被覆の**原理**自体（被覆・ヒッティング問題の LP 緩和、Lovász）は教科書的。
   jlevy 自身が「確立された分数被覆原理の新しい実例であって、新しい原理ではない」と明言している。
   この枠組みを採用するのが妥当。
