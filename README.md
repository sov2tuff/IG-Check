[README.md](https://github.com/user-attachments/files/34553880/README.md)
# Instagram Username Checker

A simple console tool that checks a list of Instagram usernames and tells you which ones are available.

Load a `.txt` file, watch the live dashboard, and get a `result.txt` with every available username. It can also generate random usernames for you to check.

## Features

- **Bulk checking** from a `.txt` file (one username per line, drag and drop supported)
- **Live dashboard** with progress bar, AVAILABLE / TAKEN / ERROR counters, speed, ETA and recent results
- **Username generator** with four types: letters only, letters + numbers, letters + numbers + special characters, or a mix of all
- **Valid names only:** generated usernames follow Instagram's rules (3-30 characters, `a-z 0-9 . _`, no `..`, never digits only, never start or end with `.` or `_`)
- **Results never overwritten:** saved as `result.txt`, then `result (1).txt`, `result (2).txt`, and so on
- **Safe stop:** press `Ctrl+C`, or even close the window, and everything checked so far is saved
- **Adjustable delay** between requests (1, 2 or 3 seconds) to stay gentle

**NOTE: Alot of the usernames that are sent as "AVAILABLE" may actually be unavailable due to the account that had that username being banned. Currently, with a simple tool like this, it cannot differ between banned and unavailable accounts so it just marks them as AVAILABLE. In simple words, this tool is a checker which checks username availability for instagram. it doesnt actually give you 100% accurate results, it just shortlists the list of usernames which u can then manually check yourself.**

## Setup

Requires Python 3.9+.

```
pip install -r requirements.txt
python main.py
```

## Usage

1. Run `python main.py`.
2. Pick **1** to check a list: drag your `.txt` file into the window and press Enter.
3. Or pick **2** to generate usernames, choose a type, length and amount, and optionally check them right away.
4. Use **3** for settings (delay between requests).

## Output files

Saved next to `main.py`:

| File | Contents |
| --- | --- |
| `result.txt` | Every AVAILABLE username |
| `errors.txt` | Usernames that couldn't be checked (only created if there were errors), so you can re-run them |
| `generated_usernames.txt` | The most recently generated list |

## Good to know

- **AVAILABLE** means Instagram shows no live profile for that name. Banned or reserved names look the same to Instagram, so a few AVAILABLE names may still not be registrable.
- **ERROR** usually means Instagram didn't return a normal page (for example it is rate limiting you). Wait a bit, increase the delay, and re-run `errors.txt`.
- Names are checked one at a time. Instagram can change how its site responds at any time, which may break the checker.
- Automated requests may go against Instagram's terms. Use this tool responsibly and at your own risk.

---

Made by @sovvxe
