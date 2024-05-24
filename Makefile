FILE_URL := https://filesamples.com/samples/video/mkv/sample_1280x720_surfing_with_audio.mkv

TEST_FILE := tests/file.mkv

TEST_DIR := tests

.PHONY: test

test: $(TEST_FILE)
	pytest $(TEST_DIR)

$(TEST_FILE):
	@if [ ! -f $(TEST_FILE) ]; then \
		echo "Downloading $(TEST_FILE)..."; \
		curl -sSL $(FILE_URL) -o $(TEST_FILE); \
	else \
		echo "$(TEST_FILE) already exists. Skipping download."; \
	fi

clean:
	rm -f $(TEST_FILE)
