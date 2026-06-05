# ==============================================================================
# Aceh Resilience Monitor (ARM) - Automation Makefile
# ==============================================================================
# Manual shortcut commands to run, deploy, and monitor the ARM system easily.
# ==============================================================================

# Load environment variables from .env file if it exists
ifneq (,$(wildcard ./.env))
    include .env
    export
endif

# Variables (Azure & Pipeline Configuration)
# Default values can be overridden by environment variables or .env file
CONNECTION_STRING ?= $(ARM_AZURE_CONNECTION_STRING)
FUNCTION_APP ?= $(ARM_AZURE_FUNCTION_APP)
RESOURCE_GROUP ?= $(ARM_AZURE_RESOURCE_GROUP)
FUNCTION_NAME ?= $(ARM_AZURE_FUNCTION_NAME)
APP_INSIGHTS_ID ?= $(ARM_AZURE_APP_INSIGHTS_ID)
SUBSCRIPTION_ID ?= $(ARM_AZURE_SUBSCRIPTION_ID)

.PHONY: help run-local serve test evaluate-baseline upload-dashboard deploy-functions trigger-cloud monitor-logs check-mlflow check-blob fix-cors validate-json fix-active-run fix-msi

# Default target
help:
	@echo "================================================================================"
	@echo " 🚀 Aceh Resilience Monitor (ARM) Command Shortcuts"
	@echo "================================================================================"
	@echo "Pengoperasian Lokal:"
	@echo "  make run-local         - Jalankan ETL, Anomali, & Model Prophet secara lokal"
	@echo "  make serve             - Jalankan web server lokal di port 8000"
	@echo "  make test              - Jalankan seluruh unit tests (Pytest)"
	@echo "  make evaluate-baseline - Jalankan komparasi baseline (Naive vs SMA vs EMA vs Prophet)"
	@echo "  make validate-json     - Validasi sintaks dashboard_data.json lokal & cloud"
	@echo ""
	@echo "Deployment & Sinkronisasi Cloud:"
	@echo "  make upload-dashboard  - Unggah aset dasbor lokal & data ke Azure Storage (\$web)"
	@echo "  make deploy-functions  - Publish kode lokal ke Azure Function App"
	@echo "  make trigger-cloud     - Pemicu eksekusi pipeline harian di cloud secara manual"
	@echo ""
	@echo "Pemantauan & Diagnostics:"
	@echo "  make monitor-logs      - Lihat log Application Insights real-time di cloud"
	@echo "  make check-mlflow      - Lihat daftar run eksperimen MLflow di Azure ML Studio"
	@echo "  make check-blob        - Periksa metadata file dashboard_data.json di Storage"
	@echo ""
	@echo "Troubleshooting & Perbaikan:"
	@echo "  make fix-cors          - Perbaiki aturan CORS di Azure Storage Account"
	@echo "  make fix-active-run    - Tutup paksa run MLflow yang terjebak status 'RUNNING'"
	@echo "  make fix-msi           - Atur ulang Managed Identity & Role Assignment Functions"
	@echo "================================================================================"

# --- Pengoperasian Lokal ---

run-local:
	python3 -m scripts.prepare_dashboard_data

serve:
	python3 -m http.server 8000 --directory dashboard

test:
	pytest -v

evaluate-baseline:
	python3 scripts/evaluate_baseline.py

validate-json:
	@echo "--- Memvalidasi berkas lokal ---"
	python3 -c "import json; json.load(open('dashboard/dashboard_data.json')); print('✅ JSON Lokal Valid!')"
	@echo "--- Memvalidasi berkas cloud ---"
	@mkdir -p scratch
	az storage blob download \
		--container-name '$$web' \
		--name dashboard_data.json \
		--connection-string "$(CONNECTION_STRING)" \
		--file scratch/check.json && \
	python3 -c "import json; json.load(open('scratch/check.json')); print('✅ JSON Cloud Valid!')"

# --- Deployment & Sinkronisasi Cloud ---

upload-dashboard:
	az storage blob upload-batch \
		--destination '$$web' \
		--source dashboard/ \
		--connection-string "$(CONNECTION_STRING)" \
		--overwrite

deploy-functions:
	cd azure-functions && func azure functionapp publish $(FUNCTION_APP)

trigger-cloud:
	@echo "Mendapatkan master key untuk $(FUNCTION_APP)..."
	@master_key=$$(az functionapp keys list --name $(FUNCTION_APP) --resource-group $(RESOURCE_GROUP) --query masterKey -o tsv); \
	if [ -z "$$master_key" ]; then \
		echo "❌ Gagal mendapatkan Master Key. Pastikan Anda sudah login via 'az login'."; \
		exit 1; \
	fi; \
	echo "Master Key didapat. Mengirim trigger POST ke $(FUNCTION_NAME)..."; \
	curl -i -X POST \
		-H "x-functions-key: $$master_key" \
		-H "Content-Type: application/json" \
		-d "{}" \
		https://$(FUNCTION_APP).azurewebsites.net/admin/functions/$(FUNCTION_NAME)

# --- Pemantauan & Diagnostics ---

monitor-logs:
	az monitor app-insights query \
		--app $(APP_INSIGHTS_ID) \
		--analytics-query "traces | order by timestamp desc | project timestamp, message | take 30" \
		--query "tables[0].rows" -o json

check-mlflow:
	python3 -c "
	from azureml.core import Workspace
	import mlflow
	try:
	    ws = Workspace.from_config()
	    mlflow.set_tracking_uri(ws.get_mlflow_tracking_uri())
	    experiment = mlflow.get_experiment_by_name('arm-daily-production')
	    runs = mlflow.search_runs(experiment_ids=[experiment.experiment_id], order_by=['start_time DESC'], max_results=10)
	    for index, row in runs.iterrows():
	        run_name = row.get('tags.mlflow.runName') or row.get('run_name')
	        print(f'Run ID: {row.get(\"run_id\")[:8]}... | Name: {run_name:<40} | Status: {row.get(\"status\")}')
	except Exception as e:
	    print('❌ Eror saat membaca MLflow:', e)
	"

check-blob:
	az storage blob show \
		--container-name '$$web' \
		--name dashboard_data.json \
		--connection-string "$(CONNECTION_STRING)" \
		--query "{lastModified:properties.lastModified, size_in_bytes:properties.contentLength}"

# --- Troubleshooting & Perbaikan ---

fix-cors:
	@echo "--- Memperbaiki CORS di Azure Storage Account ---"
	az storage cors add \
		--methods GET \
		--origins "https://thankful-river-084494910.7.azurestaticapps.net" "http://localhost:8000" "http://localhost:3000" \
		--services b \
		--connection-string "$(CONNECTION_STRING)"
	@echo "--- Memperbaiki CORS di Azure Function App ---"
	az functionapp cors add \
		--name $(FUNCTION_APP) \
		--resource-group $(RESOURCE_GROUP) \
		--allowed-origins "https://portal.azure.com"

fix-active-run:
	python3 -c "
	import mlflow
	from azureml.core import Workspace
	try:
	    ws = Workspace.from_config()
	    mlflow.set_tracking_uri(ws.get_mlflow_tracking_uri())
	    if mlflow.active_run():
	        mlflow.end_run(status='FAILED')
	        print('✅ Berhasil menutup paksa active run yang menggantung!')
	    else:
	        print('Tidak ada active run lokal.')
	except Exception as e:
	    print('❌ Gagal memeriksa active run:', e)
	"

fix-msi:
	@echo "Mengaktifkan System-Assigned Managed Identity pada $(FUNCTION_APP)..."
	principal_id=$$(az functionapp identity assign --name $(FUNCTION_APP) --resource-group $(RESOURCE_GROUP) --query principalId -o tsv); \
	if [ -z "$$principal_id" ]; then \
		echo "❌ Gagal mendapatkan Principal ID."; \
		exit 1; \
	fi; \
	echo "Principal ID didapat: $$principal_id"; \
	echo "Assigning role 'Contributor' ke resource group scope..."; \
	az role assignment create \
		--assignee "$$principal_id" \
		--role "Contributor" \
		--scope "/subscriptions/$(SUBSCRIPTION_ID)/resourceGroups/$(RESOURCE_GROUP)"
