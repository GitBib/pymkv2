FILES_BASE_URL := https://raw.githubusercontent.com/GitBib/pymkv-files/master
FILE_URL := $(FILES_BASE_URL)/file.mkv
FILE_TWO_URL := $(FILES_BASE_URL)/file_2.mkv

TEST_FILE := tests/file.mkv
TEST_TWO_FILE := tests/file_2.mkv

TEST_DIR := tests/

# --fail makes curl exit non-zero on HTTP errors instead of writing the error
# body into the target file, which would leave a corrupt "MKV" behind.
CURL := curl -sSL --fail --retry 3 --retry-delay 2

.PHONY: test clean

test: $(TEST_FILE) $(TEST_TWO_FILE)
	@echo "Running mkvmerge -V..."
	@mkvmerge -V
	@echo "Verifying test files..."
	@for f in $(TEST_FILE) $(TEST_TWO_FILE); do \
		mkvmerge -J $$f | grep -q '"recognized"[[:space:]]*:[[:space:]]*true' \
			|| { echo "ERROR: $$f is not a valid Matroska file. Run 'make clean' and retry."; exit 1; }; \
	done
	uv run pytest --cov=pymkv $(TEST_DIR) --cov-report=xml --junitxml=test-results/junit.xml

# Download to a .part file and rename only on success, so an interrupted
# download never leaves a partial file that make would treat as up to date.
$(TEST_FILE):
	@echo "Downloading $(TEST_FILE)..."
	@$(CURL) $(FILE_URL) -o $(TEST_FILE).part
	@mv $(TEST_FILE).part $(TEST_FILE)
	@echo "Downloaded $(TEST_FILE)"

$(TEST_TWO_FILE):
	@echo "Downloading $(TEST_TWO_FILE)..."
	@$(CURL) $(FILE_TWO_URL) -o $(TEST_TWO_FILE).part
	@mv $(TEST_TWO_FILE).part $(TEST_TWO_FILE)
	@echo "Downloaded $(TEST_TWO_FILE)"

clean:
	rm -f $(TEST_FILE) $(TEST_FILE).part $(TEST_TWO_FILE) $(TEST_TWO_FILE).part
