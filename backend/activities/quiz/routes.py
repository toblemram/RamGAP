# -*- coding: utf-8 -*-
"""
Quiz Routes
===========
Flask Blueprint for quiz scoreboard.

Endpoints:
    GET  /api/quiz/scores           — Get scoreboard (top scores, per-user bests)
    POST /api/quiz/scores           — Save a new quiz score
"""

from flask import Blueprint, jsonify, request
from sqlalchemy import func

from core.database import get_db_session
from core.models import QuizScore

quiz_bp = Blueprint('quiz', __name__, url_prefix='/api/quiz')


@quiz_bp.route('/scores', methods=['GET'])
def get_scores():
    """Return the scoreboard.

    Query params:
        quiz_name  — filter by quiz (default: NS-EN 1997-1)
        limit      — max rows for the all-time list (default: 50)
    """
    quiz_name = request.args.get('quiz_name', 'NS-EN 1997-1')
    limit = min(int(request.args.get('limit', 50)), 200)

    db = get_db_session()
    try:
        # All-time top scores
        top = (
            db.query(QuizScore)
            .filter(QuizScore.quiz_name == quiz_name)
            .order_by(QuizScore.pct.desc(), QuizScore.score.desc(), QuizScore.created_at.desc())
            .limit(limit)
            .all()
        )

        # Per-user best score
        subq = (
            db.query(
                QuizScore.username,
                func.max(QuizScore.pct).label('best_pct'),
            )
            .filter(QuizScore.quiz_name == quiz_name)
            .group_by(QuizScore.username)
            .subquery()
        )
        user_bests_rows = (
            db.query(QuizScore)
            .join(subq, (QuizScore.username == subq.c.username) & (QuizScore.pct == subq.c.best_pct))
            .filter(QuizScore.quiz_name == quiz_name)
            .order_by(QuizScore.pct.desc(), QuizScore.score.desc())
            .all()
        )
        # Deduplicate to one entry per user (the latest among ties)
        seen = set()
        user_bests = []
        for row in user_bests_rows:
            if row.username not in seen:
                user_bests.append(row.to_dict())
                seen.add(row.username)

        return jsonify({
            'top_scores': [s.to_dict() for s in top],
            'user_bests': user_bests,
        })
    finally:
        db.close()


@quiz_bp.route('/scores', methods=['POST'])
def save_score():
    """Save a quiz score.

    JSON body:
        username   — str, required
        score      — int, required
        total      — int, required
        max_streak — int, optional (default 0)
        quiz_name  — str, optional (default NS-EN 1997-1)
    """
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    score = data.get('score')
    total = data.get('total')

    if not username or score is None or total is None:
        return jsonify({'error': 'username, score and total are required'}), 400

    if not isinstance(score, int) or not isinstance(total, int) or total <= 0:
        return jsonify({'error': 'score and total must be positive integers'}), 400

    pct = round(score / total * 100, 1)
    max_streak = int(data.get('max_streak', 0))
    quiz_name = data.get('quiz_name', 'NS-EN 1997-1')

    db = get_db_session()
    try:
        entry = QuizScore(
            username=username,
            quiz_name=quiz_name,
            score=score,
            total=total,
            pct=pct,
            max_streak=max_streak,
        )
        db.add(entry)
        db.commit()
        return jsonify(entry.to_dict()), 201
    except Exception as exc:
        db.rollback()
        return jsonify({'error': str(exc)}), 500
    finally:
        db.close()
