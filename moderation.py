import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

# Helper functions
def query_database(query, args=(), one=False):
    conn = sqlite3.connect('prompts.db')
    cursor = conn.cursor()
    cursor.execute(query, args)
    rv = cursor.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv

def execute_database(query, args=()):
    conn = sqlite3.connect('prompts.db')
    cursor = conn.cursor()
    cursor.execute(query, args)
    conn.commit()
    conn.close()

# Main Application Class
class AdminApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Admin Panel")
        self.geometry("800x600")

        # Search frame
        search_frame = tk.Frame(self)
        search_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(search_frame, text="Search: ").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        tk.Entry(search_frame, textvariable=self.search_var).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        tk.Button(search_frame, text="Search", command=self.search_users).pack(side=tk.LEFT)

        # User list frame
        self.user_list_frame = tk.Frame(self)
        self.user_list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.user_list = ttk.Treeview(self.user_list_frame, columns=("id", "username", "discord_username", "banned"), show="headings")
        self.user_list.heading("id", text="ID")
        self.user_list.heading("username", text="Username")
        self.user_list.heading("discord_username", text="Discord Username")
        self.user_list.heading("banned", text="Banned")
        self.user_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(self.user_list_frame, orient=tk.VERTICAL, command=self.user_list.yview)
        self.user_list.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.user_list.bind("<Double-1>", self.view_user)

        # Actions frame
        actions_frame = tk.Frame(self)
        actions_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Button(actions_frame, text="Ban/Unban User", command=self.toggle_ban_user).pack(side=tk.LEFT, padx=5)
        tk.Button(actions_frame, text="Delete User", command=self.delete_user).pack(side=tk.LEFT, padx=5)
        tk.Button(actions_frame, text="Delete User Prompts", command=self.delete_user_prompts).pack(side=tk.LEFT, padx=5)
        tk.Button(actions_frame, text="Delete User Comments", command=self.delete_user_comments).pack(side=tk.LEFT, padx=5)
        tk.Button(actions_frame, text="Delete User Votes", command=self.delete_user_votes).pack(side=tk.LEFT, padx=5)
        tk.Button(actions_frame, text="Specific Data", command=self.specific_data).pack(side=tk.LEFT, padx=5)

        self.load_users()

    def load_users(self):
        self.user_list.delete(*self.user_list.get_children())
        users = query_database("SELECT id, username, discord_username, banned FROM users")
        for user in users:
            self.user_list.insert("", "end", values=user)

    def search_users(self):
        search_term = self.search_var.get()
        self.user_list.delete(*self.user_list.get_children())
        users = query_database("SELECT id, username, discord_username, banned FROM users WHERE username LIKE ?", (f"%{search_term}%",))
        for user in users:
            self.user_list.insert("", "end", values=user)

    def view_user(self, event):
        selected_item = self.user_list.selection()
        if selected_item:
            user_id = self.user_list.item(selected_item[0], "values")[0]
            UserDetails(self, user_id)

    def toggle_ban_user(self):
        selected_item = self.user_list.selection()
        if selected_item:
            user_id = self.user_list.item(selected_item[0], "values")[0]
            user = query_database("SELECT banned FROM users WHERE id = ?", (user_id,), one=True)
            if user:
                new_status = not user[0]
                execute_database("UPDATE users SET banned = ? WHERE id = ?", (new_status, user_id))
                self.load_users()

    def delete_user(self):
        selected_item = self.user_list.selection()
        if selected_item:
            user_id = self.user_list.item(selected_item[0], "values")[0]
            if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this user and all associated data?"):
                execute_database("DELETE FROM comments WHERE user_id = ?", (user_id,))
                execute_database("DELETE FROM votes WHERE user_id = ?", (user_id,))
                execute_database("DELETE FROM prompts WHERE user_id = ?", (user_id,))
                execute_database("DELETE FROM users WHERE id = ?", (user_id,))
                self.load_users()

    def delete_user_prompts(self):
        selected_item = self.user_list.selection()
        if selected_item:
            user_id = self.user_list.item(selected_item[0], "values")[0]
            if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete all prompts for this user?"):
                execute_database("DELETE FROM prompts WHERE user_id = ?", (user_id,))
                self.load_users()

    def delete_user_comments(self):
        selected_item = self.user_list.selection()
        if selected_item:
            user_id = self.user_list.item(selected_item[0], "values")[0]
            if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete all comments for this user?"):
                execute_database("DELETE FROM comments WHERE user_id = ?", (user_id,))
                self.load_users()

    def delete_user_votes(self):
        selected_item = self.user_list.selection()
        if selected_item:
            user_id = self.user_list.item(selected_item[0], "values")[0]
            if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete all votes for this user?"):
                execute_database("DELETE FROM votes WHERE user_id = ?", (user_id,))
                self.load_users()

    def specific_data(self):
        selected_item = self.user_list.selection()
        if selected_item:
            user_id = self.user_list.item(selected_item[0], "values")[0]
            SpecificDataWindow(self, user_id)

class UserDetails(tk.Toplevel):
    def __init__(self, parent, user_id):
        super().__init__(parent)
        self.title("User Details")
        self.geometry("600x400")

        self.user_id = user_id

        # Fetch user details
        user = query_database("SELECT username, discord_username, bio, avatar_url, banned FROM users WHERE id = ?", (user_id,), one=True)

        if user:
            tk.Label(self, text=f"Username: {user[0]}").pack(anchor="w", padx=10, pady=5)
            tk.Label(self, text=f"Discord Username: {user[1]}").pack(anchor="w", padx=10, pady=5)
            tk.Label(self, text=f"Bio: {user[2]}").pack(anchor="w", padx=10, pady=5)
            tk.Label(self, text=f"Avatar URL: {user[3]}").pack(anchor="w", padx=10, pady=5)
            tk.Label(self, text=f"Banned: {'Yes' if user[4] else 'No'}").pack(anchor="w", padx=10, pady=5)

            # Prompts list frame
            tk.Label(self, text="Prompts:").pack(anchor="w", padx=10, pady=5)
            self.prompts_list = tk.Listbox(self)
            self.prompts_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            self.load_prompts()

    def load_prompts(self):
        self.prompts_list.delete(0, tk.END)
        prompts = query_database("SELECT id, title, content FROM prompts WHERE user_id = ?", (self.user_id,))
        for prompt in prompts:
            self.prompts_list.insert(tk.END, f"ID: {prompt[0]} - Title: {prompt[1]}")

class SpecificDataWindow(tk.Toplevel):
    def __init__(self, parent, user_id):
        super().__init__(parent)
        self.title("Specific Data")
        self.geometry("800x600")
        # maximize window
        self.state('zoomed')

        self.user_id = user_id

        # Tab control
        tab_control = ttk.Notebook(self)
        self.comments_tab = ttk.Frame(tab_control)
        self.prompts_tab = ttk.Frame(tab_control)
        self.votes_tab = ttk.Frame(tab_control)
        tab_control.add(self.comments_tab, text="Comments")
        tab_control.add(self.prompts_tab, text="Prompts")
        tab_control.add(self.votes_tab, text="Votes")
        tab_control.pack(expand=1, fill="both")

        # Comments list
        self.comments_list = ttk.Treeview(self.comments_tab, columns=("id", "prompt_id", "message", "created_at"), show="headings")
        self.comments_list.heading("id", text="ID")
        self.comments_list.heading("prompt_id", text="Prompt ID")
        self.comments_list.heading("message", text="Message")
        self.comments_list.heading("created_at", text="Created At")
        self.comments_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        comments_scrollbar = ttk.Scrollbar(self.comments_tab, orient=tk.VERTICAL, command=self.comments_list.yview)
        self.comments_list.configure(yscroll=comments_scrollbar.set)
        comments_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Button(self.comments_tab, text="Delete Comment", command=self.delete_comment).pack(pady=5)

        # Prompts list
        self.prompts_list = ttk.Treeview(self.prompts_tab, columns=("id", "title", "content"), show="headings")
        self.prompts_list.heading("id", text="ID")
        self.prompts_list.heading("title", text="Title")
        self.prompts_list.heading("content", text="Content")
        self.prompts_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        prompts_scrollbar = ttk.Scrollbar(self.prompts_tab, orient=tk.VERTICAL, command=self.prompts_list.yview)
        self.prompts_list.configure(yscroll=prompts_scrollbar.set)
        prompts_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Button(self.prompts_tab, text="Delete Prompt", command=self.delete_prompt).pack(pady=5)

        # Votes list
        self.votes_list = ttk.Treeview(self.votes_tab, columns=("id", "prompt_id", "vote_type", "created_at"), show="headings")
        self.votes_list.heading("id", text="ID")
        self.votes_list.heading("prompt_id", text="Prompt ID")
        self.votes_list.heading("vote_type", text="Vote Type")
        self.votes_list.heading("created_at", text="Created At")
        self.votes_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        votes_scrollbar = ttk.Scrollbar(self.votes_tab, orient=tk.VERTICAL, command=self.votes_list.yview)
        self.votes_list.configure(yscroll=votes_scrollbar.set)
        votes_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Button(self.votes_tab, text="Delete Vote", command=self.delete_vote).pack(pady=5)

        self.load_specific_data()

    def load_specific_data(self):
        self.load_comments()
        self.load_prompts()
        self.load_votes()

    def load_comments(self):
        self.comments_list.delete(*self.comments_list.get_children())
        comments = query_database("SELECT id, prompt_id, message, created_at FROM comments WHERE user_id = ?", (self.user_id,))
        for comment in comments:
            self.comments_list.insert("", "end", values=comment)

    def load_prompts(self):
        self.prompts_list.delete(*self.prompts_list.get_children())
        prompts = query_database("SELECT id, title, content FROM prompts WHERE user_id = ?", (self.user_id,))
        for prompt in prompts:
            self.prompts_list.insert("", "end", values=prompt)

    def load_votes(self):
        self.votes_list.delete(*self.votes_list.get_children())
        votes = query_database("SELECT id, prompt_id, vote FROM votes WHERE user_id = ?", (self.user_id,))
        for vote in votes:
            self.votes_list.insert("", "end", values=vote)

    def delete_comment(self):
        selected_item = self.comments_list.selection()
        if selected_item:
            comment_id = self.comments_list.item(selected_item[0], "values")[0]
            if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this comment?"):
                execute_database("DELETE FROM comments WHERE id = ?", (comment_id,))
                self.load_comments()

    def delete_prompt(self):
        selected_item = self.prompts_list.selection()
        if selected_item:
            prompt_id = self.prompts_list.item(selected_item[0], "values")[0]
            if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this prompt?"):
                execute_database("DELETE FROM prompts WHERE id = ?", (prompt_id,))
                self.load_prompts()

    def delete_vote(self):
        selected_item = self.votes_list.selection()
        if selected_item:
            vote_id = self.votes_list.item(selected_item[0], "values")[0]
            if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this vote?"):
                execute_database("DELETE FROM votes WHERE id = ?", (vote_id,))
                self.load_votes()

if __name__ == "__main__":
    app = AdminApp()
    app.mainloop()
