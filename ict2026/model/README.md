# edge/model

모델 파일 저장 위치

- 기본 경로: `edge/model/best_model.pth`
- 파이프라인 실행 시 변경 가능:

```bash
python -m edge.pipeline.loop --mode yolo --model-path <모델경로> ...
```

실제 가중치 파일로 교체한 뒤 실행
