import json
import os
import urllib.request
from collections import Counter
from pathlib import Path

GITHUB_API = "https://api.github.com"
TOKEN = os.environ["GH_STATS_TOKEN"]

OUTPUT = Path("profile/projects-by-language.svg")


def github_get(url):
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {TOKEN}",
            "X-GitHub-Api-Version": "2026-03-10",
            "User-Agent": "github-profile-stats",
        },
    )

    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))


def get_repositories():
    repositories = []
    page = 1

    while True:
        url = (
            f"{GITHUB_API}/user/repos"
            f"?visibility=all"
            f"&affiliation=owner"
            f"&per_page=100"
            f"&page={page}"
        )

        data = github_get(url)

        if not data:
            break

        repositories.extend(data)

        if len(data) < 100:
            break

        page += 1

    return repositories


def calculate_languages(repositories):
    counts = Counter()

    total_projects = 0

    for repo in repositories:

        # Ignore forks
        if repo.get("fork", False):
            continue

        # Ignore archived repositories
        if repo.get("archived", False):
            continue

        language = repo.get("language")

        # A repository without a detectable primary language
        # is not included in the language distribution.
        if not language:
            continue

        counts[language] += 1
        total_projects += 1

    return counts, total_projects


def escape(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def generate_svg(counts, total_projects):

    if total_projects == 0:
        raise RuntimeError(
            "No projects with a primary language were found."
        )

    languages = counts.most_common(8)

    width = 700
    row_height = 52
    header_height = 90
    footer_height = 45

    height = (
        header_height
        + len(languages) * row_height
        + footer_height
    )

    svg = []

    svg.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
    )

    svg.append(
        '<rect width="100%" height="100%" '
        'rx="12" fill="#ffffff"/>'
    )

    svg.append(
        '<text x="35" y="42" '
        'font-family="Arial, Helvetica, sans-serif" '
        'font-size="25" '
        'font-weight="700" '
        'fill="#2678e8">'
        'Projects by Primary Language'
        '</text>'
    )

    y = header_height

    for language, count in languages:

        percentage = (count / total_projects) * 100

        svg.append(
            f'<text x="35" y="{y}" '
            'font-family="Arial, Helvetica, sans-serif" '
            'font-size="15" '
            'fill="#4b5563">'
            f'{escape(language)}'
            '</text>'
        )

        bar_x = 200
        bar_width = 330
        bar_height = 10

        svg.append(
            f'<rect x="{bar_x}" y="{y - 12}" '
            f'width="{bar_width}" '
            f'height="{bar_height}" '
            'rx="5" fill="#dedede"/>'
        )

        filled_width = bar_width * percentage / 100

        svg.append(
            f'<rect x="{bar_x}" y="{y - 12}" '
            f'width="{filled_width:.2f}" '
            f'height="{bar_height}" '
            'rx="5" fill="#2678e8"/>'
        )

        svg.append(
            f'<text x="560" y="{y}" '
            'font-family="Arial, Helvetica, sans-serif" '
            'font-size="14" '
            'fill="#4b5563">'
            f'{percentage:.1f}%'
            '</text>'
        )

        svg.append(
            f'<text x="625" y="{y}" '
            'font-family="Arial, Helvetica, sans-serif" '
            'font-size="13" '
            'fill="#6b7280">'
            f'({count})'
            '</text>'
        )

        y += row_height

    svg.append(
        f'<text x="35" y="{height - 20}" '
        'font-family="Arial, Helvetica, sans-serif" '
        'font-size="13" '
        'fill="#6b7280">'
        f'Based on {total_projects} projects'
        '</text>'
    )

    svg.append("</svg>")

    return "\n".join(svg)


def main():

    print("Fetching repositories from GitHub...")

    repositories = get_repositories()

    print(f"Repositories returned by GitHub: {len(repositories)}")

    counts, total_projects = calculate_languages(
        repositories
    )

    print("\nProject language distribution:")

    for language, count in counts.most_common():

        percentage = (count / total_projects) * 100

        print(
            f"{language}: "
            f"{count} projects "
            f"({percentage:.1f}%)"
        )

    print(
        f"\nProjects included: {total_projects}"
    )

    svg = generate_svg(
        counts,
        total_projects
    )

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT.write_text(
        svg,
        encoding="utf-8"
    )

    print(
        f"\nSuccessfully generated: {OUTPUT}"
    )


if __name__ == "__main__":
    main()
