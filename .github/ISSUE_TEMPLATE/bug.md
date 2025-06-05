---
name: バグ報告
about: バグ修正依頼（Claude Code向け）
title: '[BUG] '
labels: bug
assignees: ''
---

## 🐛 バグ詳細

### 現在の動作
<!-- 実際に起きている問題の詳細 -->

### 期待する動作  
<!-- あるべき正しい動作 -->

### 影響範囲
- [ ] **機能影響**: どの機能が使えないか
- [ ] **データ影響**: データ破損の可能性
- [ ] **パフォーマンス影響**: 性能低下の有無

## 🔍 再現手順

1. 
2. 
3. 
4. エラー発生

### 再現環境
- **OS**: Ubuntu 22.04 / macOS 13 / Windows 11
- **Python**: 3.12.x
- **compare-regions-jp**: v0.x.x
- **関連ライブラリ**: geopandas v0.14.x, osmnx v1.6.x

### エラー出力
```
エラーメッセージやスタックトレースをここに貼り付け
```

## 🔧 問題分析

### 推定原因
<!-- 技術的な原因の推測 -->

### 関連ファイル
- [ ] `src/compare_regions_jp/xxx/yyy.py` - 行番号: XX
- [ ] `tests/xxx/test_yyy.py` - テストケース不足?

## 💡 修正方針

### 推奨アプローチ
1. **入力バリデーション強化**
2. **エラーハンドリング追加**  
3. **テストケース追加**

### 修正箇所（推定）
```python
# 修正前
def problematic_function(param):
    return process(param)  # エラーが発生する箇所

# 修正後（案）
def problematic_function(param):
    if not validate_param(param):
        raise ValidationError("Invalid parameter")
    try:
        return process(param)
    except SomeError as e:
        logger.error(f"Processing failed: {e}")
        raise ProcessingError("Failed to process") from e
```

## 🧪 修正後テスト要求

### 追加すべきテストケース
- [ ] **再現テスト**: 報告されたバグの再現
- [ ] **回帰テスト**: 修正により他が壊れないことの確認  
- [ ] **エッジケース**: 類似の問題の予防

### テストデータ
```python
# 問題を引き起こすテストデータ
problematic_data = {
    "param": "バグを引き起こす値"
}
```

## ✅ 修正完了の確認項目

### 機能要件
- [ ] 報告されたバグが修正されている
- [ ] 元の機能が正常に動作する
- [ ] パフォーマンスが劣化していない

### 品質要件
- [ ] **テスト**: 追加テストが通過
- [ ] **カバレッジ**: 維持または向上
- [ ] **型チェック**: mypy通過
- [ ] **回帰テスト**: 既存機能に影響なし

## 💻 Claude Code 修正指示案

```bash
claude-code "Issue #XX対応: [バグ概要]を修正してください

【問題】
- ファイル: src/compare_regions_jp/xxx/yyy.py
- 症状: [現在の動作]
- 期待: [期待する動作]

【修正方針】
- [推定原因] を解決
- [修正箇所] にエラーハンドリング追加

【テスト要求】
- バグ再現テストを tests/xxx/test_yyy.py に追加
- 修正後に全テスト通過確認

【参考】
- Issue: https://github.com/user/compare-regions-jp/issues/XX
- エラーログ: [エラー出力の内容]
"
```