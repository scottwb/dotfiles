;##############################################################################
;# init.el
;#
;# This is an example init.el that includes major modes for various languages
;# such as C/C++, Perl, Javascript, Ruby, RHTML, etc. with indentation
;# styles configured to the Ranger Coding Style conventions.
;#
;# It also contains some personl preferences which are either self-explanitory
;# or clearly marked.
;#
;##############################################################################

;;; Make both OPTION and COMMAND keys on Mac work as a Meta key
(setq mac-option-modifier 'meta)
(setq mac-command-modifier 'meta)

;;; Make HOME and END keys work like they should on a Mac.
(define-key global-map [home] 'beginning-of-line)
(define-key global-map [end] 'end-of-line)

;;; Ask me before quitting.
(setq confirm-kill-emacs 'y-or-n-p)

;;; C-c-c to comment a selected region.
(global-set-key '[?\C-c ?c] 'comment-region)

;;; Enable SHIFT-Arrow to select text.
(cua-mode t)

;;; Disable cua-mode's C-x, C-x, and C-v for cut/copy/paste. You need to do
;;; this if you prefer to use Emacs C-x and C-c based key bindings to operate
;;; on rectangles (such as C-x-r-t), but if you prefer standard
;;; cut/copy/paste keys, remove this line.
(setq cua-enable-cua-keys nil)

;;; TODO:
;;;
;;;   * Must fix M-g goto-line!
;;;   * Why doesn't C-b toggle back to previously-used buffer?
;;;   * Make status bar show parent dir name.
;;;   * See if I can get the tabbar back
;;;   * Figure out a good grep mode
;;;   * Figure out how to make it so that when I turn off viper-mode
;;;     it doesn't turn itself back on automatically with the next new
;;;     buffer.
;;;

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; Common Stuff
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

;;; Turn off stupid package signature crap.
(setq package-get-require-signed-base-updates nil)

;;; Add ~/.emacs.d to the load path for custom libraries.
(add-to-list 'load-path "~/.emacs.d/vendor")

;;; Setup the keyboard so the delete key on both the regular keyboard
;;; and the keypad delete the character under the cursor and to the
;;; right under X-Windows, instead of the default backspace behavoir.
(global-set-key [delete] 'delete-char)
(global-set-key [kp-delete] 'delete-char)

;;; Make it so that CTRL-DEL deletes the whole forward word.
(global-set-key '[(control delete)] 'kill-word)
(global-set-key '[(control kp-delete)] 'kill-word)

(global-set-key [f4] 'toggle-viper-mode)

(global-set-key [f5] 'make-frame)
(global-set-key [(shift f5)] 'delete-frame)

;;; Turn on font-lock mode (syntax highlighting).
(global-font-lock-mode t)

;;; Always end a file with a newline
(setq require-final-newline t)

;;; Don't let 'next-line' add new lines in buffer
(setq next-line-add-newlines nil)

;;; Enable wheelmouse support by default
(mouse-wheel-mode t)

;;; Set mouse wheel to scroll by one line to begin with, progressively
;;; incrementing that amount by one for scroll events in rapid succession.
(setq mouse-wheel-scroll-amount '(1 ((shift) . 1) ((control)  nil)))

;;; Don't restrict the depth of the minibuffer
(setq minibuffer-max-depth nil)

;;; Don't use tabs, use spaces! (default tab-width of 2)
(setq-default indent-tabs-mode nil)
(setq default-tab-width 2)
(setq tab-offset 2)

;;; Always clean up bad whitespace (like trailing whitespace)
(require 'whitespace)
(setq whitespace-action '(auto-cleanup))
(setq whitespace-style '(trailing space-before-tab indentation empty space-after-tab))
(global-whitespace-mode)

;;; Replace all tabs with spaces when saving.
;;; REVISIT: this is not tested yet
;(defun my-untabify ()
;  (save-excursion
;    (goto-char (point-min))
;    (while (re-search-forward "[ \t]+$" nil t)
;      (delete-region (match-beginning 0) (match-end 0)))
;    (goto-char (point-min))
;    (if (search-forward "\t" nil t)
;        (untabify (1- (point)) (point-max)))) nil)
;
;(add-hook 'before-save-hook
;          (lambda ()
;            (if (string-match "makefile.*mode" (symbol-name major-mode))
;                (message "Makefile mode, so no untabify!")
;              (make-local-variable 'write-contents-hooks)
;              (add-hook 'write-contents-hooks 'my-untabify))))


;;; Turn on paren highlighting
;(setq show-paren-style 'parenthesis)
;(setq show-paren-style 'expression)
(setq show-paren-style 'mixed)
(setq show-paren-delay 0)
(show-paren-mode t)


;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; Make scrolling with more like it does in Visual Studio
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
(defun my-scroll-up ()
  "Scrolls selected buffer one line up without moving point"
  (interactive)
  (scroll-up 1))

(defun my-scroll-down ()
  "Scrolled selected buffer one line down without moving point"
  (interactive)
  (scroll-down 1))

(global-set-key [(control up)] 'my-scroll-down)
(global-set-key [(control down)] 'my-scroll-up)


;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; Perl Editing Mode Configuration
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
(add-hook 'cperl-mode-hook 'my-cperl-mode-hook)
(defun my-cperl-mode-hook ()
  (fume-mode t)  ; turn on function-menu
  (setq indent-tabs-mode nil))

;;; Make Perl mode automatically reindent the current line, and then
;;; automatically indent the new line to the correct position
(add-hook 'cperl-mode-hook
          '(lambda ()
             (local-set-key "\C-m"
                            'reindent-then-newline-and-indent)))


;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; C/C++ Editing Mode Configuration
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;(require 'func-menu)

;;; Make sure .h files are treated as C++
(setq auto-mode-alist (cons '("\\.h$" . c++-mode) auto-mode-alist))

;;; Make C mode automatically reindent the current line, and then
;;; automatically indent the new line to the correct position
(add-hook 'c-mode-hook
          '(lambda ()
             (local-set-key "\C-m"
                            'reindent-then-newline-and-indent)))

;;; Make C++ mode automatically reindent the current line, and then
;;; automatically indent the new line to the correct position
(add-hook 'c++-mode-hook
          '(lambda ()
             (local-set-key "\C-m"
                            'reindent-then-newline-and-indent)))

;;; Turn on function menus
(add-hook 'c-mode-common-hook 'my-c-mode-common-hook)
(defun my-c-mode-common-hook ()
  ;(fume-mode t)
  (setq indent-tabs-mode nil))

;;; Helper function for computing the relative indent offset of C++ labels,
;;; which we always want to be absolute zero -- so it just returns the
;;; negative of the current indent level.
(defun my-label-offset (syntax-info)
  (- (cdr syntax-info)))

;;; Ranger indentation style for C/C++ Mode
(custom-set-variables
 '(c-insert-tab-function (quote insert-tab))
 '(c-basic-offset 4)
 '(indent-tabs-mode nil)

 ;; C/C++ Mode indentation offsets
 '(c-offsets-alist
   (quote (
           ;; construct definitions
           (topmost-intro . 0)
           (topmost-intro-cont . 0)

           ;; regular arg list
           (arglist-intro . +)                ; first arg in decl
           (arglist-cont . 0)                 ; susequent args
           (arglist-cont-nonempty . +)        ; subsequent args
           (arglist-close . 0)                ; arg list close paren

           ;; KnR decl arg list
           (knr-argdecl-intro . +)            ; first arg in decl
           (knr-argdecl . 0)                  ; subsequent args

           ;; statement blocks
           (statement-block-intro . +)        ; first line in block

           ;; substatement blocks
           (substatement-open . 0)            ; for/if/while open parent

           ;; labels
           (label . (my-label-offset))        ; regular label
           (case-label . 0)                   ; case label
           (access-label . (my-label-offset)) ; C++ public/private/protected

           ;; inline functions
           (inline-open . 0)                  ; open brace for inline func

           ;; macros
           (cpp-macro-cont . +)               ; continued lines of macro
           )))
)


;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; Go Editing Mode Configuration
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
(require 'go-mode-load)
(defun my-go-mode-hook()
  (add-hook 'before-save-hook 'gofmt-before-save)
  (setq tab-width 4 indent-tabs-mode 1))
(add-hook 'go-mode-hook 'my-go-mode-hook)


;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; YAML Editing Mode Configuration
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
(require 'yaml-mode)
(add-to-list 'auto-mode-alist '("\\.yml$" . yaml-mode))
(add-hook 'yaml-mode-hook
          '(lambda ()
             (define-key yaml-mode-map "\C-m" 'newline-and-indent)))


;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; Python Editing Mode Configuration
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
(add-hook 'python-mode-hook
          '(lambda ()
             (define-key python-mode-map "\C-m" 'newline-and-indent)))


;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; Javascript Editing Mode Configuration
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

;;; Make Javascript mode automatically reindent the current line, and then
;;; automatically indent the new line to the correct position
(add-hook 'js-mode-hook
          '(lambda ()
             (local-set-key "\C-m"
                            'reindent-then-newline-and-indent)))
(setq js-indent-level 2)
(add-to-list `auto-mode-alist '("\\.json" . js-mode))


;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; TypeScript Editing Mode Configuration
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
(require 'typescript-mode)


;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; SGML Editing Mode Configuration (HTML/XML)
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
(add-to-list 'auto-mode-alist '("\\.html" . sgml-mode))
(add-to-list 'auto-mode-alist '("\\.xml" . xml-mode))

;;; SGML highlighting and indentation
(setq sgml-markup-faces
      '((start-tag . font-lock-function-name-face)
        (end-tag . font-lock-function-name-face)
        (comment . font-lock-comment-face)
        (pi . bold)
        (sgml . bold)
        (doctype . bold)
        (entity . font-lock-type-face)
        (shortref . font-lock-function-name-face)))
(setq sgml-set-face t)
(setq-default sgml-indent-data t)


;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; PHP Editing Mode Configuration
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
(require 'php-mode)
(setq php-mode-force-pear t)
(add-hook 'php-mode-hook
          '(lambda ()
             (local-set-key (kbd "RET") 'newline-and-indent)
             (setq indent-tabs-mode nil)
             (setq tab-width 4)
             (setq c-basic-offset 4)))
(add-to-list 'auto-mode-alist '("\\.php$" . php-mode))
(add-to-list 'auto-mode-alist '("\\.inc" . php-mode))


;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; CoffeeScript Editing Mode Configuration
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
(require 'coffee-mode)
(add-to-list 'auto-mode-alist '("\\.coffee$" . coffee-mode))
(add-to-list 'auto-mode-alist '("Cakefile" . coffee-mode))


;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; C# Editing Mode Configuration
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
(autoload 'csharp-mode "csharp-mode" "Major mode for editing C# code." t)
(setq auto-mode-alist
   (append '(("\\.cs$" . csharp-mode)) auto-mode-alist))


;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; HAML/SASS Editing Mode Configuration
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
(require 'haml-mode nil 't)
(add-to-list 'auto-mode-alist '("\\.haml$" . haml-mode))

(require 'sass-mode nil 't)
(add-to-list 'auto-mode-alist '("\\.sass$" . sass-mode))

;;; Also, make SCSS files use CSS mode
(add-to-list 'auto-mode-alist '("\\.scss$" . css-mode))


;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; Jade Template Editing Mode Configuration
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
(require 'sws-mode)
(require 'jade-mode)
(require 'stylus-mode)
(add-to-list 'auto-mode-alist '("\\.styl$" . stylus-mode))
(add-to-list 'auto-mode-alist '("\\.jade$" . jade-mode))


;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; Cucumber Feature Mode Configuration
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
(add-to-list 'load-path "~/.emacs.d/vendor/cucumber.el")
(require 'feature-mode)
(add-to-list 'auto-mode-alist '("\.feature$" . feature-mode))


;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; Ruby/Rails Editing Mode Configuration
;;
;; .rb - Uses ruby-mode. This is pretty good, except that
;;       I haven't yet figured out how to make multi-line
;;       parameter lists indent consistent with the Ranger
;;       Coding Style conventions. I also haven't figured
;;       out to enable some additional cool ruby-mode features like:
;;         * eval-block
;;         * run under inf-ruby
;;         * ruby debugger
;;         * jump to error
;;         * tab completion abbreviation snippets
;;         * etc.
;;
;; .rhtml - Uses mmm-mode with psgml-mode as the major
;;          mode and ruby-mode as the minor mode. This does
;;          not automatically recognize ERb chunks as you
;;          type, you need to hit:
;;            C-c % C-5   -- to re-highlight the block
;;          or
;;            C-c % C-b   -- to re-highlight the buffer
;;          This does on ok job of indenting HTML code,
;;          but not very good at indenting the ERb code,
;;          but this is the best setup I could
;;          get after spending tons of time experimenting
;;          with various rhtml highlighting options.
;;
;; NOTE: This does not currently use any of the "rails-mode"
;;       package, which sounds cool -- integrates with rails
;;       directory structure to provide auto switching
;;       between model/view/controller related functions,
;;       etc, and integrations with the ruby generate scripts --
;;       because I could not really get it working.
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
(require 'ruby-mode)

(add-to-list 'auto-mode-alist '("\\.rake$" . ruby-mode))

;;; Set .rhtml files to use SGML major mode
(add-to-list 'auto-mode-alist '("\\.rhtml" . sgml-mode))

;;; Setup MMM-mode to use ruby-mode as the minor-mode for editing
;;; rhtml files.
;(require 'mmm-mode)
;(mmm-add-classes
; '((ruby :front "<%[=#]?"
;        :back "-?%>"
;        :match-face (("<%#" . mmm-comment-submode-face)
;                     ("<%=" . mmm-output-submode-face)
;                     ("<%"  . mmm-code-submode-face))
;        :submode ruby-mode)))
;(add-to-list 'mmm-mode-ext-classes-alist '(sgml-mode nil ruby))
;(setq mmm-global-mode 'maybe)

;;; Make Ruby mode automatically reindent the current line, and then
;;; automatically indent the new line to the correct position
(add-hook 'ruby-mode-hook
          '(lambda ()
             (local-set-key "\C-m"
                            'reindent-then-newline-and-indent)))


;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; Misc Plugins
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

;; Create, browse, view gists on gist.github.com.
(require 'gist)

;;; Enable dabbrev: dynamic C-<tab> auto completion of commonly
;;; used words found in the open buffers.
(global-set-key (kbd "C-<tab>") 'dabbrev-expand)
(define-key minibuffer-local-map (kbd "C-<tab>") 'dabbrev-expand)

;;; Enable pop-up tooltips for dabbrev on the M-/ key.
(require 'dabbrev-expand-multiple)
(global-set-key "\M-/" 'dabbrev-expand-multiple)

;;; Move the backup *~ files into a single backups directory instead of
;;; littering the filesystem with them. Also version the backups and onlyu
;;; keep a finite number of backup versions.
(require 'backup-dir)
(make-variable-buffer-local 'backup-inhibited)
(setq bkup-backup-directory-info
      '((t "~/.emacs.d/backups" ok-create full-path prepend-name)))
(setq delete-old-versions t
      kept-old-versions 1
      kept-new-versions 3
      version-control t)
(defun make-backup-file-name (FILE)
  (let ((dirname (concat "~/.emacs.d/backups"
                         (format-time-string "%y/%m/%d/"))))
    (if (not (file-exists-p dirname))
        (make-directory dirname t))
    (concat dirname (file-name-nondirectory FILE))))


;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; EditorConfig
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
(require 'editorconfig)
(editorconfig-mode 1)


;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; Personal Preferences
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

;; Change default colors
;(set-face-background 'default "white")
;(set-face-foreground 'default "black")

;;; REVISIT: custom-set-variables and custom-set faces are usually set
;;;          in custom.el. May need to find a better way to do this
;;;          so that changing the fonts/settings from XEmacs menus
;;;          don't screw this up.

;;; Misc custom options
(custom-set-variables
 '(font-lock-maximum-decoration t)
 '(font-lock-use-colors t)
 '(line-number-mode t)
 '(column-number-mode t)
 '(font-lock-use-fonts nil)
 '(bar-cursor nil)
 '(tab-width 8)
 '(ps-print-color-p nil)
 '(lisp-tag-indentation 4)
 '(user-mail-address "scottwb@scottwb.net" t)
 '(query-user-mail-address nil)
)

;;; Custom font options
(custom-set-faces
 '(info-node ((t (:bold t))))
 '(cperl-nonoverridable-face ((((class color) (background light)) (:foreground "blue"))))
 '(cperl-hash-face ((((class color) (background light)) (:foreground "Red" :bold t))))
 '(hyper-apropos-section-heading ((t (:bold t))))
 '(shell-output-face ((t nil)) t)
 '(italic ((t (:underline nil))) t)

 ; Parenthesis-matching highlight color
 '(show-paren-match-face ((((class color) (background light)) (:background "lightblue"))))

 ; Incremental search highlight
 '(isearch ((((class color) (background light)) (:background "paleturquoise"))))
 '(isearch-lazy-highlight-face ((((class color) (background light)) (:foreground "red"))))

 ; Code syntax highlighting colors
 '(font-lock-string-face ((((class color) (background light)) (:foreground "red3"))))
 '(font-lock-doc-string-face ((((class color) (background light)) nil)))
 '(font-lock-type-face ((((class color) (background light)) (:foreground "CadetBlue"))))
 '(font-lock-variable-name-face ((((class color) (background light)) (:foreground "black"))))
 '(font-lock-function-name-face ((((class color) (background light)) (:foreground "brown4"))))
 '(font-lock-constant-face ((((class color) (background light)) (:foreground "red4"))))
 '(font-lock-keyword-face ((((class color) (background light)) (:foreground "blue"))))
 '(font-lock-comment-face ((((class color) (background light)) (:foreground "green4"))))

 '(semantic-dirty-token-face ((((class color) (background light)) nil)))
 '(cvs-handled-face ((((class color) (background light)) (:foreground "blue")))))

;;; Themes
(add-to-list 'custom-theme-load-path "~/.emacs.d/themes")
(load-theme 'dracula t)

;;; Default Font Size
(set-face-attribute 'default nil :height 160)
