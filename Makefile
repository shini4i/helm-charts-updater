.DEFAULT_GOAL := run

.PHONY: run
run:
	@poetry run helm-charts-updater
	@rm -rf charts
