# 先行研究の確認（2026-09-13 調査）

本リポジトリで確定した 9 件が既発表でないことを文献調査で確認した。

## 結論: 9 件とも発表時点で新規

**追記（2026-09-21）.** n = 26 と n = 29 は、その後
[tokoharu/square-packing-density-bounds](https://github.com/tokoharu/square-packing-density-bounds)
の長方形密度証明書（5.508 / 5.71）に上回られた。下記の比較は本リポジトリの証明書が
公開された時点のもので、証明としての有効性は変わらないが、この 2 件は現在の最良値ではない。

| n | 本研究 | 既知最良下界 | 出典 | 改善 |
|---|---|---|---|---|
| 26 | **5.45** | 5.3918 = 2√2+(27+2√10)/13 | Green 2000（Friedman への私信）、DS7 Theorem 9 (k=5) | +0.058 |
| 29 | **5.57** | 5.5117 = 2√2+6/√5 | Green 2000、DS7 Theorem 10 (k=5)、n=28 からの単調性 | +0.058 |
| 39 | **6.5** | 6.3506 = 2√2+(113+10√3)/37 | Green 2000、DS7 Theorem 9 (k=6)、n=37 からの単調性 | +0.149 |
| 53 | **7.38** | 7.3246 = 1+√(53−2⌊√53⌋+1) | Nagamochi 2005 の閉じた式。これを上回る記録なし | +0.055 |
| 55 | **7.54** | 7.4807 = 1+√(55−2⌊√55⌋+1) | Nagamochi 2005 の閉じた式。これを上回る記録なし | +0.059 |
| 56 | **7.62** | 7.5574 = 1+√(56−2⌊√56⌋+1) | Nagamochi 2005 の閉じた式。これを上回る記録なし | +0.063 |
| 69 | **8.41** | 8.3485 = 1+√(69−2⌊√69⌋+1) | Nagamochi 2005 の閉じた式。これを上回る記録なし | +0.062 |
| 70 | **8.55** | 8.4162 = 1+√(70−2⌊√70⌋+1) | Nagamochi 2005 の閉じた式。これを上回る記録なし | +0.134 |
| 72 | **8.61** | 8.5498 = 1+√(72−2⌊√72⌋+1) | Nagamochi 2005 の閉じた式。これを上回る記録なし | +0.060 |

後の 6 件は先の 3 件と性格が異なる。n = 26, 29, 39 では従来値が Green の未公刊の
私信だったのに対し、n = 53, 55, 56, 69, 70, 72 には Green の値がそもそも記録されて
おらず、独立検証済みの最良値は Nagamochi の閉じた式である。したがってこの 6 件は、
根拠を辿れない値ではなく、公表され検証された結果を上回っている。

n = 56 と n = 72 は、我々自身の先行する証明書が単調性で与えていた値も上回る。
s(55) ≥ 7.54 は s(56) を 7.54 に、s(70) ≥ 8.55 は s(72) を 8.55 に留めていた。
ただしこの 2 件は他の下界と違い、波及する項目を持たない。Nagamochi の式は
n = 57 以降で 7.62 を、n = 73 以降で 8.61 を既に上回るためである。

## 根拠

### 1. Friedman のサーベイ DS7 は 2009-08-14 版が最新
Electronic Journal of Combinatorics の Dynamic Survey DS7 は 2009 年以降改訂されていない。
その Table 2 が n ≤ 100 の下界の権威ある一覧であり、該当行は上表の通り。
**n ≤ 100 の下界を系統的に与えた文献はこれが唯一。**

### 2. Green の値は私信であり証明が公開されていない
DS7 の出典はすべて "Green, private communication (2000)" で、幾何学的証明は回収できていない。
jlevy/squares の `packing/frontier/ds7-lower-bound-audit.json` も Green の値を
「source-reported; proof not independently verified」として扱い、独立検証済みの値は
Nagamochi 系の 1+√(n−1) 型に留めている（n=26: 5.1231、n=29: 5.4721、n=39: 6.2915）。
同プロジェクトの `research-2026-09-07-n26-best-known-audit.md` は
「Green の 5.3918 は私信で証明が回収できていない」と明記している。

**したがって本研究の 3 件は、完全に検証可能な証明書を伴う点で Green の値より強い。**

### 3. Kingbird のページは上界のみ
David Ellsworth 管理の記録表は「最小の既知の正方形」= 上界の一覧で、下界は載っていない。
関連する上界は n=26: 7/2+3√2/2 ≈ 5.6213（Friedman 1997）、
n=29: 5.93383（Thomas Schadt, 2025-12）、n=39: 6.81072（Schadt, 2026-01）。

### 4. 重み付き unavoidable set 系の先行研究はすべて小さい n
| 研究 | 対象 n | 手法 |
|---|---|---|
| Stromquist 1984/2003 | 11 | unavoidable points（創始） |
| Nagamochi 2005 | 一般 | unavoidable points の一般化 |
| Bentz 2010 (EJC 17 #R126) | 13, 46 | 連続変化する unavoidable 族 |
| Bentz 2016 (arXiv:1606.03746) | 22, 33 | 同上 |
| Sam Burns 2026 | 17 | weighted points（268 点、総重み 16.9476） |
| Massaccesi 2026 | 17–19 | 4.5058 |
| jlevy/squares 2026 | 11, 12, 17–21 | fractional certificate（n=11 で 1121 atoms） |

**n = 26, 29, 39 を扱ったものは存在しない。**

## 注意点
- Green の私信を「published」と呼べるかは微妙だが、いずれにせよ本研究の値が上回る。
- n=29 と n=39 の既知下界は単調性由来（n=28, n=37 から）。
  本研究の s(29) ≥ 5.57 は s(28) ≥ 5.57 を**意味しない**（含意は逆向き）。記述の際は注意。
- ResearchGate 等の壁の内側の論文本文は未確認。ただし DS7 が dynamic survey として
  下界を追跡する役割を担っており、2009 年以降 n=26/29/39 の更新が反映されていないことから、
  公表された更新はないと判断する。

## 出典
- Friedman, "Packing Unit Squares in Squares: A Survey and New Results", EJC DS7 (2009-08-14 版)
  https://www.combinatorics.org/files/Surveys/ds7/ds7v5-2009/ds7-2009.html
- Kingbird / David Ellsworth, "Squares in Squares"
  https://kingbird.myphotos.cc/packing/squares_in_squares.html
- jlevy/squares https://github.com/jlevy/squares
- Bentz, arXiv:1606.03746 / EJC 17(1) #R126
- Sam Burns, "Proposing a Better Lower Bound for n=17 Square Packing"
- Massaccesi, "Another Better Lower Bound for n=17 Square Packing"
