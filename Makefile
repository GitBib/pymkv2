FILE_URL := https://pymkv-files.bnff.website/file.mkv
FILE_TWO_URL := https://pymkv-files.bnff.website/file_2.mkv

TEST_FILE := tests/file.mkv
TEST_TWO_FILE := tests/file_2.mkv

TEST_DIR := tests/

.PHONY: test clean

test: $(TEST_FILE) $(TEST_TWO_FILE)
	@echo "Running mkvmerge -V..."
	@mkvmerge -V
	@echo "Running mkvmerge -J $(TEST_FILE)..."
	@mkvmerge -J $(TEST_FILE)
	@echo "Running mkvmerge -J $(TEST_TWO_FILE)..."
	@mkvmerge -J $(TEST_TWO_FILE)
	pytest --cov=pymkv $(TEST_DIR) --cov-report=xml --junitxml=test-results/junit.xml

$(TEST_FILE):
	@if [ ! -f $(TEST_FILE) ]; then \
		echo "Downloading $(TEST_FILE)..."; \
		curl -sSL $(FILE_URL) -o $(TEST_FILE); \
		echo "Downloaded to $$(realpath $(TEST_FILE))"; \
	else \
		echo "$(TEST_FILE) already exists. Skipping download."; \
	fi

$(TEST_TWO_FILE):
	@if [ ! -f $(TEST_TWO_FILE) ]; then \
		echo "Downloading $(TEST_TWO_FILE)..."; \
		curl -sSL $(FILE_TWO_URL) -o $(TEST_TWO_FILE); \
		echo "Downloaded to $$(realpath $(TEST_TWO_FILE))"; \
	else \
		echo "$(TEST_TWO_FILE) already exists. Skipping download."; \
	fi

clean:
	rm -f $(TEST_FILE) $(TEST_TWO_FILE)
