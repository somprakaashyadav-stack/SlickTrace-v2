"""
SlickTrace v2 — Candidates & Physical Consistency Scoring API Endpoint

Provides candidate retrieval and ranking based on Physical Consistency Score.
Mandatory Notice:
"This score measures consistency with the reconstructed physical scenario. It is not a determination of responsibility."
"""
from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.candidate import CandidateVessel
from app.models.ais_query import AISQuery
from app.schemas.candidate import CandidateResponse

router = APIRouter()


@router.get("/{incident_id}/candidates", response_model=List[CandidateResponse])
async def list_candidates(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get candidate vessels for an incident sorted by Physical Consistency Score.
    Candidates without a rank appear after ranked candidates.
    """
    result = await db.execute(
        select(CandidateVessel)
        .where(CandidateVessel.incident_id == incident_id)
        .order_by(CandidateVessel.rank.asc().nulls_last(), CandidateVessel.created_at.asc())
    )
    return result.scalars().all()


@router.get("/{incident_id}/candidates/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(
    incident_id: uuid.UUID,
    candidate_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a single candidate vessel with full physical consistency score breakdown."""
    result = await db.execute(
        select(CandidateVessel).where(
            CandidateVessel.id == candidate_id,
            CandidateVessel.incident_id == incident_id,
        )
    )
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


@router.post("/{incident_id}/candidates/rank", status_code=202)
async def trigger_candidate_ranking(
    incident_id: uuid.UUID,
    ais_query_id: Optional[uuid.UUID] = Query(None, description="Optional AIS query ID to score"),
    db: AsyncSession = Depends(get_db),
):
    """
    Triggers physical consistency ranking for all candidates of the incident.
    Calculates 10 physical consistency factors, Isolation Forest anomaly features,
    and produces explainable factor contributions.
    """
    if not ais_query_id:
        result = await db.execute(
            select(AISQuery.id)
            .where(AISQuery.incident_id == incident_id)
            .order_by(AISQuery.executed_at.desc())
            .limit(1)
        )
        ais_query_id = result.scalar_one_or_none()
        if not ais_query_id:
            raise HTTPException(status_code=404, detail="No AIS query found for this incident.")

    try:
        from app.tasks.scoring_task import run_scoring
        task = run_scoring.delay(str(incident_id), str(ais_query_id))
        return {
            "status": "ranking_dispatched",
            "incident_id": str(incident_id),
            "ais_query_id": str(ais_query_id),
            "task_id": str(task.id),
            "disclaimer": "This score measures consistency with the reconstructed physical scenario. It is not a determination of responsibility.",
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to dispatch physical consistency ranking: {e}")


@router.post("/{incident_id}/candidates/{candidate_id}/verify", response_model=CandidateResponse)
async def run_counterfactual(
    incident_id: uuid.UUID,
    candidate_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Run counterfactual forward verification for a candidate vessel.
    Simulates forward drift from candidate position and checks consistency with observed spill geometry.
    """
    result = await db.execute(
        select(CandidateVessel).where(
            CandidateVessel.id == candidate_id,
            CandidateVessel.incident_id == incident_id,
        )
    )
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    try:
        from app.tasks.scoring_task import run_counterfactual_task
        run_counterfactual_task.delay(str(candidate_id))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to dispatch verification: {e}")

    return candidate
