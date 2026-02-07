# ADR-001: 技術スタック選定

## ステータス
Accepted

## コンテキスト
「大人が無料で、スキマ時間に、1戦だけ気軽に遊べるゲームマッチングWebアプリ」のMVPを構築する。

## 決定

### フロントエンド
- **Vue 3 + Vite + TypeScript + Tailwind CSS v4 + Pinia**
- 理由: 軽量で高速な開発体験、Composition APIによる型安全性

### バックエンド
- **FastAPI + SQLAlchemy (async) + Alembic + Pydantic v2**
- 理由: 非同期I/O、自動OpenAPI生成、型安全なバリデーション

### データベース
- **PostgreSQL 17**
- 理由: `SELECT FOR UPDATE SKIP LOCKED` による競合制御、信頼性

### 認証
- **ニックネーム入力 + HttpOnlyセッションCookie**
- 理由: MVP段階では最小の摩擦で開始できることを優先

### レート制限
- **slowapi**
- 理由: FastAPIとの統合が簡単、IP/エンドポイント単位の制限

## 結果
- ローカル開発環境で「募集→マッチ→チャット→クローズ→フィードバック」のフルフローが動作
- テストはpytest（バックエンド）で22件パス
