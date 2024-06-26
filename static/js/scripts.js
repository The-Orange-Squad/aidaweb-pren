document.addEventListener("DOMContentLoaded", function () {
    // Modal Functionality
    var modals = document.querySelectorAll('.modal');
    var closeButtons = document.querySelectorAll('.close');

    closeButtons.forEach(function (btn) {
        if (btn) {
            btn.addEventListener('click', function () {
                this.closest('.modal').style.display = 'none';
            });
        }
    });

    document.querySelectorAll('[data-toggle="modal"]').forEach(function (trigger) {
        if (trigger) {
            trigger.addEventListener('click', function () {
                var targetId = this.getAttribute('data-target');
                var targetElement = document.querySelector(targetId);
                if (targetElement) {
                    targetElement.style.display = 'block';
                }
            });
        }
    });

    document.querySelectorAll('[data-dismiss="modal"]').forEach(function (dismiss) {
        if (dismiss) {
            dismiss.addEventListener('click', function () {
                this.closest('.modal').style.display = 'none';
            });
        }
    });

    window.addEventListener('click', function (event) {
        modals.forEach(function (modal) {
            if (event.target == modal) {
                modal.style.display = 'none';
            }
        });
    });

    // Voting
    document.querySelectorAll('.vote-btn').forEach(function (button) {
        if (button) {
            button.addEventListener('click', function () {
                var promptId = this.getAttribute('data-prompt-id');
                var voteType = this.getAttribute('data-vote-type');
                var parent = this.closest('.prompt-container') || this.closest('.prompt-item') || document;

                fetch('/vote', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: `prompt_id=${promptId}&vote_type=${voteType}`
                })
                    .then(response => response.json())
                    .then(data => {
                        var voteRatioElement = parent.querySelector('#voteRatio');
                        if (voteRatioElement) {
                            voteRatioElement.textContent = `Upvotes: ${data.upvotes} | Downvotes: ${data.downvotes} | Total: ${data.total}`;
                        }
                    });
            });
        }
    });

    // Sort Prompts
    var updateSortingButton = document.querySelector('#updateSorting');
    if (updateSortingButton) {
        updateSortingButton.addEventListener('click', function () {
            var sortOption = document.querySelector('#sortOption').value;
            window.location.href = `/explore?sort_by=${sortOption}`;
        });
    }

    // Load More Prompts
    var loadMoreButton = document.querySelector('#loadMorePrompts');
    if (loadMoreButton) {
        var promptsContainer = document.querySelector('#promptsContainer');
        var offset = 40;
        var sortBy = document.querySelector('#sortOption').value || 'latest';

        loadMoreButton.addEventListener('click', function () {
            fetch('/load_more_prompts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `offset=${offset}&sort_by=${sortBy}`
            })
                .then(response => response.json())
                .then(prompts => {
                    prompts.forEach(prompt => {
                        promptsContainer.insertAdjacentHTML('beforeend', `
                            <section class="prompt-item">
                                <h2><a href="/prompt/${prompt[0]}">${prompt[2]}</a></h2>
                                <textarea readonly class="previewprompt">${prompt[3]}</textarea>
                                <div class="prompt-footers">
                                    <span>👍 ${prompt[4] - prompt[5]}</span>
                                    <span>👁️ ${prompt[6]}</span>
                                </div>
                            </section>
                        `);
                    });

                    offset += 40;
                });
        });
    }

    // Load More Search Results
    var loadMoreSearchResultsButton = document.querySelector('#loadMoreSearchResults');
    if (loadMoreSearchResultsButton) {
        var searchQuery = loadMoreSearchResultsButton.getAttribute('data-query');
        var promptsContainer = document.querySelector('#promptsContainer');
        var offset = 40;

        loadMoreSearchResultsButton.addEventListener('click', function () {
            fetch('/search_load_more', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `query=${searchQuery}&offset=${offset}`
            })
                .then(response => response.json())
                .then(prompts => {
                    prompts.forEach(prompt => {
                        promptsContainer.insertAdjacentHTML('beforeend', `
                            <section class="prompt-item">
                                <h2><a href="/prompt/${prompt[0]}">${prompt[2]}</a></h2>
                                <textarea readonly class="previewprompt">${prompt[3]}</textarea>
                                <div class="prompt-footers">
                                    <span>👍 ${prompt[4] - prompt[5]}</span>
                                    <span>👁️ ${prompt[6]}</span>
                                </div>
                            </section>
                        `);
                    });

                    offset += 40;
                });
        });
    }

    // Search Prompts
    var searchButton = document.querySelector('#searchPrompts');
    if (searchButton) {
        searchButton.addEventListener('click', function () {
            var searchQuery = document.querySelector('#searchPrompt').value;
            window.location.href = `/search?query=${searchQuery}`;
        });
    }

    var copyButton = document.querySelector('.copy-button');
    if (copyButton) {
        copyButton.addEventListener('click', function () {
            var text = copyButton.getAttribute('data-clipboard-text');
            if (text) {
                navigator.clipboard.writeText(text).then(function () {
                    console.log('Async: Copying to clipboard was successful!');
                }, function (err) {
                    console.error('Async: Could not copy text: ', err);
                    // fallback to execCommand
                    var textArea = document.createElement("textarea");
                    textArea.value = text;
                    document.body.appendChild(textArea);
                    textArea.select();
                    document.execCommand('copy');
                    document.body.removeChild(textArea);
                });
            }
        });
    }

    var sideBar = document.querySelector('.side-bar');
    if (sideBar) {
        var all_a = sideBar.querySelectorAll('a');
        all_a.forEach(function (a) {
            // find their parents
            var parent = a.parentElement;
            // add click event to parent to click the child
            parent.addEventListener('click', function () {
                a.click();
            });
        });
    }
});
