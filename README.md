# 🎓 숙명여대 사용자 데이터 기반 프로젝트 매칭 추천 시스템

학생의 관심 분야와 활동 이력을 기반으로 적합한 프로젝트를 추천하는 추천 시스템

## 📌 Project Overview

본 프로젝트는 학생들의 관심사, 역량, 활동 이력을 기반으로 적합한 프로젝트를 추천합니다.
- 콘텐츠 기반 필터링 (Content-based Filtering) 
- 협업 필터링 (Collaborative Filtering)
- 위 2개를 결합한 Hybrid Recommendation System

## ❓ Problem Definition

학교 내 프로젝트나 대외 활동은 다양하게 존재하지만,
- 자신에게 맞는 프로젝트를 빠르게 찾기 어렵고
- 정보 탐색 비용이 높아 참여 기회를 놓치는 경우가 많습니다.

데이터 기반 추천 시스템을 통해 프로젝트 탐색 과정을 효율화하고자 합니다.

## 🗂️ Data Generation

### User / Project Data
- GPT 기반 데이터 생성
- 사전 정의된 컬럼 구조 및 제약 사항 반영
- User 데이터: 5,000개
- Project 데이터: 5,000개

### Interaction Data
- 룰 기반 점수 계산 방식 사용
- User–Project 적합도 점수화 : role / skill / interest 매칭 가중치 적용
- 랜덤 User 2,800명 × 모든 Project 조합 점수 계산
- User별 상위 Project 50개 중 랜덤 선택 후 interaction 생성
- 총 15,000개 interaction 데이터 생성

## 🧠 Recommendation System

본 프로젝트에서는 Hybrid Recommendation System을 구현했습니다.

### (1) Content-Based Filtering (CBF)
- 사용자 관심사 및 역량과 프로젝트 요구 조건 간 유사도 계산
- 신규 사용자(Cold Start)에도 추천 가능

### (2) Collaborative Filtering (CF)
- User–Project interaction 이력을 기반으로 유사 사용자 탐색
- 실제 사용자 행동 패턴 반영

### (3) Hybrid Filtering
- 콘텐츠 기반 필터링과 협업 필터링의 결과를 결합한 알고리즘
- Cold Start 문제 완화 및 추천 정확도 향상

## 👥 Team
남민서, 백서연, 윤소영, 임소정, 제혜림
