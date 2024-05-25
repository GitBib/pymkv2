FILE_URL := https://filesamples.com/samples/video/mkv/sample_1280x720_surfing_with_audio.mkv
FILE_TWO_URL := https://filesamples.com/samples/video/mkv/sample_960x400_ocean_with_audio.mkv

TEST_FILE := tests/file.mkv
TEST_TWO_FILE := tests/file_2.mkv

TEST_DIR := tests

.PHONY: test clean

test: $(TEST_FILE) $(TEST_TWO_FILE)
	pytest $(TEST_DIR)

$(TEST_FILE):
	@if [ ! -f $(TEST_FILE) ]; then \
		echo "Downloading $(TEST_FILE)..."; \
		curl -sSL $(FILE_URL) -o $(TEST_FILE); \
	else \
		echo "$(TEST_FILE) already exists. Skipping download."; \
	fi

$(TEST_TWO_FILE):
	@if [ ! -f $(TEST_TWO_FILE) ]; then \
		echo "Downloading $(TEST_TWO_FILE)..."; \
		curl -sSL $(FILE_TWO_URL) -o $(TEST_TWO_FILE); \
	else \
		echo "$(TEST_TWO_FILE) already exists. Skipping download."; \
	fi

clean:
	rm -f $(TEST_FILE) $(TEST_TWO_FILE)
