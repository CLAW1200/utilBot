import os
import app

def update_bot():
    """
    Update the bot and restart it
    """ 
    print ("Updating bot from updateBot.py")
    #end the bot 
    app.exit_bot()
    print ("Bot ended")

    # Check if the bot is up to date
    if not is_bot_version_latest():
        os.system("git pull")
        print ("Bot updated")

    #Start the bot
    print ("Starting bot")
    os.system("python3 app.py")
    print ("Bot started")
    return

def is_bot_version_latest():
    """
    Check for an update to the bot via github
    """
    # Get the current commit hash
    current_commit_hash = get_current_commit_hash()

    # Get the latest commit hash from github
    latest_commit_hash = get_latest_commit_hash()

    # Check if the bot is up to date
    if current_commit_hash == latest_commit_hash:
        return True
    else:
        return False
    
def get_current_commit_hash():
    """
    Get the current commit hash of the bot
    """
    # Get the current commit hash
    with open(".git/refs/heads/master", "r") as f:
        current_commit_hash = f.read().strip()
    print (f"Current commit hash: {current_commit_hash}")
    return current_commit_hash

def get_latest_commit_hash():
    """
    Use git command line to get the latest commit hash from github
    """
    # get latest commit hash from github
    os.system("git fetch") # fetch the latest commit hash
    os.system("git reset --hard origin/master") # reset the local repo to the latest commit hash
    with open(".git/refs/heads/master", "r") as f:
        latest_commit_hash = f.read().strip().strip("'")
    print (f"Latest commit hash: {latest_commit_hash}")

if __name__ == "__main__":
    update_bot()