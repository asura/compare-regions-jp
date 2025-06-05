---
name: 機能追加
about: 新機能の実装依頼（Claude Code向け）
title: '[FEATURE] '
labels: enhancement
assignees: ''
---

## 📋 機能概要

<!-- 実装したい機能の概要を記述 -->

## 🎯 技術仕様

### 実装場所
- [ ] **ファイル**: `src/compare_regions_jp/xxx/yyy.py`
- [ ] **クラス**: `ClassName`
- [ ] **メソッド**: `method_name(args) -> ReturnType`

### 依存関係
- [ ] **外部API**: 
- [ ] **ライブラリ**: 
- [ ] **内部モジュール**: 

### 入出力仕様
```python
# 入力例
input_data = {
    "param1": "value1",
    "param2": 123
}

# 期待出力
expected_output = {
    "result": "success",
    "data": [...]
}
```

### エラーハンドリング
- [ ] **NetworkError**: ネットワーク接続失敗時
- [ ] **ValidationError**: 入力データ不正時
- [ ] **TimeoutError**: 処理タイムアウト時

## 🧪 テスト要求

### テストファイル
- `tests/xxx/test_yyy.py`

### 必須テストケース
- [ ] **正常系**: 期待通りの動作
- [ ] **異常系**: エラーケースの処理
- [ ] **境界値**: 極端な入力での動作
- [ ] **モック**: 外部依存のモック化

### テストデータ
```python
# fixtures/sample_data.json
{
    "test_case_1": {...},
    "test_case_2": {...}
}
```

## ✅ 受け入れ基準

### 機能要件
- [ ] 仕様通りの入出力
- [ ] エラー処理が適切
- [ ] パフォーマンス要件を満たす

### 品質要件  
- [ ] **カバレッジ**: 85%以上
- [ ] **型チェック**: mypy strict通過
- [ ] **リント**: ruff チェック通過
- [ ] **docstring**: 完備

### UX要件
- [ ] ユーザフレンドリーなエラーメッセージ
- [ ] 適切なログ出力
- [ ] プログレス表示（長時間処理の場合）

## 📚 参考資料

<!-- 関連するドキュメント・API仕様等 -->

## 💻 Claude Code 実装指示案

```bash
claude-code "Issue #XX対応: [機能名]を実装してください

【実装仕様】
- ファイル: src/compare_regions_jp/xxx/yyy.py
- 詳細: [上記技術仕様の内容]

【テスト要求】  
- ファイル: tests/xxx/test_yyy.py
- ケース: [上記テストケースの内容]

【品質要求】
- カバレッジ85%以上
- mypy strict通過
- docstring完備

【参考】
- Issue: https://github.com/user/compare-regions-jp/issues/XX
- API仕様: [参考資料のリンク]
"
```